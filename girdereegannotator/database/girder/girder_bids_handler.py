import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from girder_client import GirderClient

from girdereegannotator.utils.eeg import filter_eeg

from ..models import (
    AnnotationsFile,
    AnnotationStatus,
    Asset,
    Dataset,
    EEGFile,
    EEGFileset,
    EEGFilesetIdentifier,
    GirderModel,
    User,
)
from .bids_helpers import BIDSContextManager, BIDSDerivativeContext, BIDSNamingStrategy


@dataclass
class GirderBIDSResource:
    dataset: str = "bids_dataset"
    folder: str = "bids_folder"
    file: str = "bids_item"
    asset: str = "file"


class EEGProcessor:
    def __init__(self, naming_strategy: BIDSNamingStrategy) -> None:
        self.naming = naming_strategy

    def filter_eeg_file(
        self,
        fileset_identifier: EEGFilesetIdentifier | EEGFileset,
        download_func: Any,
        upload_func: Any,
        destination_folder_id: str,
    ) -> EEGFile:
        with TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            raw_eeg_path = temp_dir_path / fileset_identifier.name
            eeg_path = temp_dir_path / self.naming.generate_filtered_eeg_name(fileset_identifier.name)

            download_func(fileset_identifier, raw_eeg_path)
            eeg = filter_eeg(raw_eeg_path, eeg_path)
            return upload_func(eeg, destination_folder_id, source_id=fileset_identifier._id)


class GirderBIDSHandler:
    def __init__(self, girder_client: GirderClient):
        self.girder_client = girder_client
        self.resource = GirderBIDSResource()

        self.context = BIDSContextManager()
        self.naming = BIDSNamingStrategy()
        self.processor = EEGProcessor(self.naming)

    def _get_user_from_id(self, user_id: str) -> User:
        user_item = self.girder_client.getUser(user_id)
        return User(
            _id=user_item["_id"],
            short_name=str(user_item["firstName"])[0].upper() + str(user_item["lastName"])[0].upper(),
            name=" ".join([str(user_item["firstName"]).capitalize(), str(user_item["lastName"]).upper()]),
            login=user_item["login"],
        )

    def _load_asset_from_file(self, file: EEGFile | EEGFileset) -> GirderModel | None:
        assets = self.girder_client.listFile(itemId=file._id)
        return next(assets, None)

    def _upload_asset_to_file(self, file_id: str, asset: Asset) -> None:
        self.girder_client.uploadFileToItem(file_id, asset.path, filename=asset.name)

    def _upload_file(
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

    def _create_derivatives_dataset(
        self, dataset: Dataset, derivatives_dataset_desc: dict[str, Any], derivatives_folder_id: str
    ) -> None:
        derivatives_dataset_desc.update({"DatasetType": "derivative", "GeneratedBy": "GirderEEGAnnotator"})
        derivatives_dataset_item = self.girder_client.createResource(
            self.resource.dataset,
            params={
                "name": "eeg_annotations",
                "parent_id": derivatives_folder_id,
                "dataset_description": json.dumps(derivatives_dataset_desc),
                "reuse_existing": True,
            },
        )
        self.context.set_dataset(
            dataset._id, BIDSDerivativeContext(derivatives_dataset_id=derivatives_dataset_item["_id"])
        )

    def _create_derivatives_folder(self, eeg_fileset: EEGFileset | EEGFilesetIdentifier) -> None:
        path_folders = self.girder_client.get(f"{self.resource.file}/{eeg_fileset._id}/path")
        fileset_context = self.context.get_fileset(eeg_fileset._id)
        folder_id = fileset_context.derivatives_dataset_id

        for folder in path_folders:
            new_folder = self.girder_client.createResource(
                self.resource.folder,
                params={"folder_id": folder_id, "name": folder["name"], "reuse_existing": True},
            )
            folder_id = new_folder["_id"]

        fileset_context.derivatives_folder_id = folder_id
        self.context.set_fileset(eeg_fileset._id, fileset_context)

    def _find_filtered_eeg_file(self, eeg_fileset: EEGFileset | EEGFilesetIdentifier) -> EEGFile | None:
        ctx = self.context.get_fileset(eeg_fileset._id)
        eeg_files = self.girder_client.get(
            self.resource.file,
            parameters={
                "dataset_id": ctx.derivatives_dataset_id,
                "source_id": eeg_fileset._id,
                "suffix": self.naming.suffix.eeg.removeprefix("_"),
                "extension": self.naming.ext.eeg.removeprefix("."),
                "limit": 1,
            },
        )
        filtered_eeg_file = eeg_files[0] if eeg_files else None

        if filtered_eeg_file is None:
            return None

        return EEGFile(_id=filtered_eeg_file["_id"], name=filtered_eeg_file["name"])

    def _find_annotations_files(
        self, eeg_fileset: EEGFileset | EEGFilesetIdentifier, eeg_id: str
    ) -> list[AnnotationsFile]:
        ctx = self.context.get_fileset(eeg_fileset._id)
        eeg_annotations_files = self.girder_client.get(
            self.resource.file,
            parameters={
                "dataset_id": ctx.derivatives_dataset_id,
                "source_id": eeg_id,
                "suffix": self.naming.suffix.annotation.removeprefix("_"),
                "extension": self.naming.ext.annotation.removeprefix("."),
                "limit": 0,
            },
        )

        return [
            AnnotationsFile(
                _id=annotations_file["_id"],
                name=annotations_file["name"],
                author=self._get_user_from_id(annotations_file["creatorId"]),
                status=AnnotationStatus(annotations_file["bids_metadata"].get("status", AnnotationStatus.IN_PROGRESS)),
            )
            for annotations_file in eeg_annotations_files
        ]

    def get_next_annotations_file_name(self, eeg_fileset: EEGFileset) -> str:
        return self.naming.get_next_annotations_file_name(eeg_fileset)

    def upload_annotations_file(
        self, eeg_fileset: EEGFileset, annotations_asset: Asset, author: User
    ) -> AnnotationsFile:
        ctx = self.context.get_fileset(eeg_fileset._id)
        file = self._upload_file(
            annotations_asset, ctx.derivatives_folder_id, source_id=eeg_fileset.eeg._id, reuse_existing=True
        )
        return AnnotationsFile(_id=file._id, name=file.name, author=author)

    def update_annotation_status(self, annotations_file: AnnotationsFile) -> AnnotationsFile:
        self.girder_client.put(
            path=f"{self.resource.file}/{annotations_file._id}/metadata",
            parameters={"metadata": json.dumps({"status": annotations_file.status.value})},
        )

    def download_file(self, file: EEGFile, path: Path, refresh: bool = False) -> Asset:
        asset = self._load_asset_from_file(file)
        if not path.exists() or refresh:
            self.girder_client.downloadFile(fileId=asset["_id"], path=str(path))
        return Asset(name=asset["name"], path=str(path))

    def get_eeg_fileset(self, eeg_fileset: EEGFileset | EEGFilesetIdentifier, compute: bool = False) -> EEGFileset:
        ctx = self.context.get_fileset(eeg_fileset._id)
        if compute and ctx.derivatives_folder_id is None:
            self._create_derivatives_folder(eeg_fileset)

        kwargs = {}
        if isinstance(eeg_fileset, EEGFilesetIdentifier) or eeg_fileset.eeg._id is None:
            filtered_eeg_file = self._find_filtered_eeg_file(eeg_fileset)
            if filtered_eeg_file is None and compute:
                filtered_eeg_file = self.processor.filter_eeg_file(
                    eeg_fileset,
                    download_func=self.download_file,
                    upload_func=self._upload_file,
                    destination_folder_id=ctx.derivatives_folder_id,
                )
        else:
            filtered_eeg_file = eeg_fileset.eeg

        if filtered_eeg_file is not None:
            kwargs.update(
                {
                    "eeg": filtered_eeg_file,
                    "annotations_files": self._find_annotations_files(eeg_fileset, filtered_eeg_file._id),
                }
            )

        return EEGFileset(
            _id=eeg_fileset._id,
            name=eeg_fileset.name,
            metadata=eeg_fileset.metadata,
            **kwargs,
        )

    def list_eeg_filesets(
        self, dataset: Dataset, offset: int = 0, limit: int = 15, search_text: str | None = None
    ) -> list[EEGFileset]:
        eeg_fileset_list = []
        dataset_ctx = self.context.get_dataset(dataset._id)

        eeg_items = self.girder_client.get(
            self.resource.file,
            parameters={
                "dataset_id": dataset._id,
                "suffix": self.naming.suffix.eeg.removeprefix("_"),
                "extension": self.naming.ext.eeg.removeprefix("."),
                "limit": limit,
                "offset": offset,
                "search_text": search_text,
            },
        )

        for eeg_item in eeg_items:
            self.context.set_fileset(
                eeg_item["_id"],
                BIDSDerivativeContext(derivatives_dataset_id=dataset_ctx.derivatives_dataset_id),
            )

            eeg_fileset_identifier = EEGFilesetIdentifier(
                _id=eeg_item["_id"],
                name=eeg_item["name"],
                metadata=eeg_item["bids_metadata"],
            )

            eeg_fileset = self.get_eeg_fileset(eeg_fileset_identifier)

            eeg_fileset_list.append(eeg_fileset)

        return eeg_fileset_list

    def list_datasets(
        self, collection_id: str, offset: int = 0, limit: int = 15, search_text: str | None = None
    ) -> list[Dataset]:
        dataset_list = []

        dataset_items = self.girder_client.get(
            self.resource.dataset,
            parameters={
                "collection_id": collection_id,
                "is_derivative": False,
                "limit": limit,
                "offset": offset,
                "search_text": search_text,
            },
        )

        for dataset_item in dataset_items:
            dataset = Dataset(
                _id=dataset_item["_id"],
                name=dataset_item["name"],
                metadata={key: str(value) for key, value in dataset_item["dataset_description"].items()},
            )
            dataset_list.append(dataset)

            self._create_derivatives_dataset(
                dataset, dataset_item["dataset_description"], dataset_item["derivatives_folder_id"]
            )

        return dataset_list
