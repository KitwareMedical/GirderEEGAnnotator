import tempfile
from asyncio import Task, to_thread
from pathlib import Path

from trame_rca.utils import RcaViewAdapter
from trame_server import Server

from girdereegannotator.database.models import (
    AnnotationFile,
    Asset,
    DatabaseError,
    EEGFileset,
    FileExtension,
)
from girdereegannotator.utils.base_logic import BaseLogic
from girdereegannotator.utils.load_status import LoadStatus

from .components import RCAView
from .eeg_viewer_ui import EEGViewerState, EEGViewerUI


class FileValidationError(Exception):
    pass


class AnnotatorLoadingError(Exception):
    pass


def is_eeg_file(file: Asset) -> bool:
    return file.name.endswith(FileExtension.eeg)


def is_annotation_file(file: Asset) -> bool:
    return file.name.endswith(FileExtension.annotation)


def upsert_annotation(annotations: list[AnnotationFile], new_annotation: AnnotationFile) -> list[AnnotationFile]:
    if any(ann._id == new_annotation._id for ann in annotations):
        return [new_annotation if ann._id == new_annotation._id else ann for ann in annotations]
    return [*annotations, new_annotation]


class EEGViewerLogic(BaseLogic[EEGViewerState]):
    view_handler: RcaViewAdapter

    def __init__(self, server: Server):
        super().__init__(server, EEGViewerState)
        self.rca_view = RCAView()
        self._current_tmpdir: tempfile.TemporaryDirectory[str] | None = None
        self.task: Task | None = None

    def set_ui(self, ui: EEGViewerUI) -> None:
        self.view_handler = ui.rca.create_view_handler(self.rca_view)

    def _cleanup_current_tmpdir(self) -> None:
        if self._current_tmpdir is not None:
            self._current_tmpdir.cleanup()
            self._current_tmpdir = None

    def _create_tmp_dir(self) -> None:
        self._cleanup_current_tmpdir()
        self._current_tmpdir = tempfile.TemporaryDirectory()

    def _set_files(self, eeg_file_path: str) -> None:
        self.rca_view.set_eeg_file(self._current_tmpdir.name, eeg_file_path)
        self.view_handler.update_size(None, self.rca_view.window_size)

    def _set_annotation_file(self, annotation_file_path: str) -> None:
        self.rca_view.set_annotation_file(annotation_file_path)

    def _load_eeg_files(
        self, eeg_fileset: EEGFileset, annotation_file: AnnotationFile | None, is_new_eeg_fileset: bool
    ) -> None:
        if is_new_eeg_fileset or self._current_tmpdir is None:
            self._create_tmp_dir()

        eeg_assets: tuple[Asset, Asset] = self.ctrl.download_eeg_files(
            eeg_fileset,
            self._current_tmpdir.name,
            annotation_file=annotation_file,
        )
        eeg_asset, annotation_asset = eeg_assets

        if not is_eeg_file(eeg_asset):
            raise FileValidationError(f"EEG file {eeg_asset.name} is invalid")

        if not is_annotation_file(annotation_asset):
            raise FileValidationError(f"Annotation file {annotation_asset.name} is invalid")

        self.data.eeg_asset = eeg_asset
        self.data.annotation_asset = annotation_asset

        try:
            if is_new_eeg_fileset:
                self._set_files(self.data.eeg_asset.path)
            self._set_annotation_file(self.data.annotation_asset.path)

        except Exception as e:
            raise AnnotatorLoadingError(f"Could not load file into annotator: {e}") from e

    def load_eeg_files(
        self, eeg_fileset: EEGFileset, annotation_file: AnnotationFile | None, is_new_eeg_fileset: bool
    ) -> Task:
        async def _load() -> None:
            try:
                updated_eeg_fileset = self.ctrl.refresh_eeg_fileset(eeg_fileset, compute_eeg=True)
                await to_thread(self._load_eeg_files, updated_eeg_fileset, annotation_file, is_new_eeg_fileset)
                self.data.load_status = LoadStatus.LOADED

            except (FileValidationError, AnnotatorLoadingError, DatabaseError) as e:
                self.data.load_status = LoadStatus.ERROR
                self.data.status_message = str(e)
                raise e

            return updated_eeg_fileset

        self.reset_state()
        self.data.load_status = LoadStatus.LOADING
        if self.task and not self.task.done():
            self.task.cancel()
        self.task = self.create_async_task(_load)
        return self.task

    def save_annotations_file(self, eeg_fileset: EEGFileset) -> None:
        if self._current_tmpdir is None:
            raise RuntimeError("Temporary directory is not initialized")

        annotation_file = self.data.annotation_asset

        self.rca_view.save_annotations_file(self.data.annotation_asset.path)

        if annotation_file.path is None or not Path(annotation_file.path).exists():
            raise FileNotFoundError(f"Annotation file ({annotation_file.path}) does not exist")

        annotation_file: AnnotationFile = self.ctrl.save_annotations_file(eeg_fileset, annotation_file)
        eeg_fileset.annotations = upsert_annotation(eeg_fileset.annotations, annotation_file)
