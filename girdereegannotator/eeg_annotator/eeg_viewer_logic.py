import tempfile
from asyncio import Task
from pathlib import Path

from trame_rca.utils import RcaViewAdapter
from trame_server import Server

from girdereegannotator.database.models import Asset, BIDSExtension, EEGFileset
from girdereegannotator.utils.base_logic import BaseLogic
from girdereegannotator.utils.load_status import LoadStatus

from .components import RCAView
from .eeg_viewer_ui import EEGViewerState, EEGViewerUI


class FileValidationError(Exception):
    pass


class AnnotatorLoadingError(Exception):
    pass


def is_eeg_file(file: Asset) -> bool:
    return file.name.endswith(BIDSExtension.eeg)


def is_annotation_file(file: Asset) -> bool:
    return file.name.endswith(BIDSExtension.annotation)


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

    def _set_files(self, file_path: str, annotation_file_path: str) -> None:
        self.rca_view.set_files(file_path, annotation_file_path)
        self.view_handler.update_size(None, self.rca_view.window_size)

    def _load_eeg_files(self, eeg_fileset: EEGFileset) -> None:
        self._create_tmp_dir()

        eeg_files: tuple[Asset, Asset] = self.ctrl.download_eeg_files(
            eeg_fileset,
            self._current_tmpdir.name,
            annotation_file=eeg_fileset.annotations[0] if eeg_fileset.annotations else None,
        )
        eeg_file, annotation_file = eeg_files

        if not is_eeg_file(eeg_file):
            raise FileValidationError(f"EEG file {eeg_file.name} is invalid")

        if not is_annotation_file(annotation_file):
            raise FileValidationError(f"Annotation file {annotation_file.name} is invalid")

        self.data.eeg_file = eeg_file
        self.data.annotation_file = annotation_file

        try:
            self._set_files(self.data.eeg_file.path, self.data.annotation_file.path)
        except Exception as e:
            raise AnnotatorLoadingError(f"Could not load file into annotator: {e}") from e

    def load_eeg_files(self, eeg_fileset: EEGFileset) -> None:
        def _load() -> None:
            try:
                self._load_eeg_files(eeg_fileset)
                self.data.load_status = LoadStatus.LOADED

            except (FileValidationError, AnnotatorLoadingError) as e:
                self.data.load_status = LoadStatus.ERROR
                self.data.status_message = str(e)
                raise e

        self.reset_state()
        self.data.load_status = LoadStatus.LOADING
        if self.task and not self.task.done():
            self.task.cancel()
        self.task = self.create_async_task(_load)

    def save_annotations(self, eeg_fileset: EEGFileset) -> None:
        if self._current_tmpdir is None:
            raise RuntimeError("Temporary directory is not initialized")

        annotation_file = self.data.annotation_file

        if annotation_file.path is None or not Path(annotation_file.path).exists():
            raise FileNotFoundError(f"Annotation file ({annotation_file.path}) does not exist")

        annotation_file = self.ctrl.save_annotations(eeg_fileset, annotation_file)
        eeg_fileset.annotations.append(annotation_file)
