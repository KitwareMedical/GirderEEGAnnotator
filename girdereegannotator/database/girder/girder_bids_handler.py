import json
import re
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from girder_client import GirderClient

from girdereegannotator.utils.eeg import filter_eeg

from ..models import (
    AnnotationFile,
    Asset,
    BIDSDataset,
    BIDSExtension,
    BIDSSuffix,
    EEGFile,
    EEGFileset,
    GirderModel,
)


@dataclass
class GirderBIDSResource:
    dataset: str = "bids_dataset"
    folder: str = "bids_folder"
    file: str = "bids_item"
    asset: str = "file"


class GirderBIDSHandler:
    def __init__(self, girder_client: GirderClient):
        self.girder_client = girder_client
        self.resource = GirderBIDSResource()
        self.suffix = BIDSSuffix()
        self.ext = BIDSExtension()

    @staticmethod
    def _extract_file_base_name(filename: str, suffix: str, extension: str) -> str:
        return filename.removesuffix(extension).removesuffix(suffix)

    def _load_asset_from_file(self, file: EEGFile) -> GirderModel | None:
        assets = self.girder_client.listFile(itemId=file._id)
        return next(assets, None)

    def _upload_asset_to_file(self, file_id: str, asset: Asset) -> None:
        self.girder_client.uploadFileToItem(file_id, asset.path, filename=asset.name)

    def _get_derivative_dataset(self, derivative_folder_id: str, dataset_desc: dict[str, Any]) -> BIDSDataset:
        derivative_dataset_desc = {**dataset_desc, "DatasetType": "derivative", "GeneratedBy": "GirderEEGAnnotator"}

        return self.girder_client.createResource(
            self.resource.dataset,
            params={
                "name": "eeg_annotations",
                "parent_id": derivative_folder_id,
                "dataset_description": json.dumps(derivative_dataset_desc),
                "reuse_existing": True,
            },
        )

    def _find_filtered_eeg_file(self, eeg_fileset: EEGFileset) -> EEGFile | None:
        eeg_files = self.girder_client.get(
            self.resource.file,
            parameters={
                "dataset_id": eeg_fileset.upload_dataset_id,
                "source_id": eeg_fileset.raw_eeg._id,
                "suffix": self.suffix.eeg.removeprefix("_"),
                "extension": self.ext.eeg.removeprefix("."),
                "limit": 1,
            },
        )
        filtered_eeg_file = eeg_files[0] if eeg_files else None

        if filtered_eeg_file is None:
            return None

        return EEGFile(_id=filtered_eeg_file["_id"], name=filtered_eeg_file["name"])

    def _find_annotation_files(self, eeg_fileset: EEGFileset) -> list[AnnotationFile]:
        eeg_annotations_files = self.girder_client.get(
            self.resource.file,
            parameters={
                "dataset_id": eeg_fileset.upload_dataset_id,
                "source_id": eeg_fileset.eeg._id,
                "suffix": self.suffix.annotation.removeprefix("_"),
                "extension": self.ext.annotation.removeprefix("."),
                "limit": 0,
            },
        )

        return [
            AnnotationFile(
                _id=annotation_file["_id"], name=annotation_file["name"], annotator_id=annotation_file["creatorId"]
            )
            for annotation_file in eeg_annotations_files
        ]

    def _create_upload_folder(self, eeg_fileset: EEGFileset) -> None:
        path_folders = self.girder_client.get(f"{self.resource.file}/{eeg_fileset.raw_eeg._id}/path")
        folder_id = eeg_fileset.upload_dataset_id

        for folder in path_folders:
            new_folder = self.girder_client.createResource(
                self.resource.folder,
                params={"folder_id": folder_id, "name": folder["name"], "reuse_existing": True},
            )
            folder_id = new_folder["_id"]

        eeg_fileset.upload_folder_id = folder_id

    def _compute_filtered_eeg_file(self, eeg_fileset: EEGFileset) -> EEGFile:
        with TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            raw_eeg_path = temp_dir_path / eeg_fileset.raw_eeg.name
            eeg_desc = "desc-filtered"
            base_name = self._extract_file_base_name(eeg_fileset.raw_eeg.name, self.suffix.eeg, self.ext.eeg)
            eeg_path = temp_dir_path / f"{base_name}_{eeg_desc}{self.suffix.eeg}{self.ext.eeg}"

            self.download_file(eeg_fileset.raw_eeg, raw_eeg_path)

            eeg = filter_eeg(raw_eeg_path, eeg_path)
            return self.upload_file(eeg, eeg_fileset.upload_folder_id, source_id=eeg_fileset.raw_eeg._id)

    def upload_file(
        self, asset: Asset, folder_id: str, source_id: str | None = None, reuse_existing: bool = False
    ) -> EEGFile:
        file = self.girder_client.createResource(
            self.resource.file,
            params={
                "name": asset.name,
                "folder_id": folder_id,
                "source_id": source_id,
                "reuse_existing": reuse_existing,
            },
        )
        self._upload_asset_to_file(file["_id"], asset)

        return EEGFile(_id=file["_id"], name=file["name"])

    def download_file(self, file: EEGFile, path: Path, refresh: bool = False) -> Asset:
        asset = self._load_asset_from_file(file)
        if not path.exists() or refresh:
            self.girder_client.downloadFile(fileId=asset["_id"], path=str(path))
        return Asset(name=asset["name"], path=str(path))

    def get_next_annotation_file_name(self, eeg_fileset: EEGFileset) -> str:
        """Return the annotation filename using the smallest available number."""
        pattern = re.compile(r"_desc-annotation(\d+)_")

        used_numbers = {
            int(match.group(1)) for annotation in eeg_fileset.annotations if (match := pattern.search(annotation.name))
        }

        next_number = 1
        while next_number in used_numbers:
            next_number += 1

        base_name = eeg_fileset.name.removesuffix(self.ext.eeg).removesuffix(self.suffix.eeg)
        annotation_desc = f"desc-annotation{next_number}"
        return f"{base_name}_{annotation_desc}{self.suffix.annotation}{self.ext.annotation}"

    def get_eeg_files(self, eeg_fileset: EEGFileset, compute: bool = False) -> None:
        if compute and eeg_fileset.upload_folder_id is None:
            self._create_upload_folder(eeg_fileset)

        if eeg_fileset.eeg.name is None:
            filtered_eeg_file = self._find_filtered_eeg_file(eeg_fileset)
            if filtered_eeg_file is None:
                if not compute:
                    return
                filtered_eeg_file = self._compute_filtered_eeg_file(eeg_fileset)
            eeg_fileset.eeg = filtered_eeg_file

        eeg_fileset.annotations = self._find_annotation_files(eeg_fileset)

    def list_eeg_filesets(self, dataset: BIDSDataset, offset: int = 0, limit: int = 15) -> list[EEGFileset]:
        eeg_fileset_list = []
        eeg_files = self.girder_client.get(
            self.resource.file,
            parameters={
                "dataset_id": dataset._id,
                "suffix": self.suffix.eeg.removeprefix("_"),
                "extension": self.ext.eeg.removeprefix("."),
                "limit": limit,
                "offset": offset,
            },
        )

        for eeg_file in eeg_files:
            eeg_fileset = EEGFileset(
                name=eeg_file["name"],
                metadata=eeg_file["meta"],
                raw_eeg=EEGFile(_id=eeg_file["_id"], name=eeg_file["name"]),
                upload_dataset_id=dataset.derivative_dataset_id,
            )
            self.get_eeg_files(eeg_fileset)

            eeg_fileset_list.append(eeg_fileset)

        return eeg_fileset_list

    def list_datasets(self, collection_id: str, offset: int = 0, limit: int = 15) -> list[BIDSDataset]:
        dataset_list = []
        for dataset in self.girder_client.get(
            self.resource.dataset,
            parameters={"collection_id": collection_id, "is_derivative": False, "limit": limit, "offset": offset},
        ):
            derivative_dataset = self._get_derivative_dataset(
                dataset["derivatives_folder_id"], dataset["dataset_description"]
            )

            dataset_list.append(
                BIDSDataset(
                    _id=dataset["_id"],
                    name=dataset["name"],
                    metadata={key: str(value) for key, value in dataset["dataset_description"].items()},
                    derivative_dataset_id=derivative_dataset["_id"],
                )
            )

        return dataset_list
