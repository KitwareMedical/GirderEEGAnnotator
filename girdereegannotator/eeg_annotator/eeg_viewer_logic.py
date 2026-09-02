import tempfile
from asyncio import Task, to_thread

from trame_rca.utils import RcaViewAdapter
from trame_server import Server
from trame_server.utils.typed_state import TypedState

from girdereegannotator.database.models import (
    AnnotationsFile,
    AnnotationStatus,
    Asset,
    DatabaseError,
    EEGFileset,
    FileExtension,
    User,
)
from girdereegannotator.utils.base_logic import BaseLogic
from girdereegannotator.utils.load_status import LoadStatus

from .components.rca_view import RCAView, RCAViewError, RCAViewMode
from .eeg_viewer_ui import EEGViewerState, EEGViewerUI


class FileValidationError(Exception):
    pass


class EEGViewerError(Exception):
    pass


def is_eeg_file(file: Asset) -> bool:
    return file.name.endswith(FileExtension.eeg)


def is_annotations_file(file: Asset) -> bool:
    return file.name.endswith(FileExtension.annotation)


class EEGViewerLogic(BaseLogic[EEGViewerState]):
    view_handler: RcaViewAdapter

    def __init__(self, server: Server):
        super().__init__(server, EEGViewerState)
        self.rca_view = RCAView()
        self._current_tmpdir: tempfile.TemporaryDirectory[str] | None = None
        self.task: Task | None = None

        self.current_user = TypedState(self.state, User)
        self.bind_changes({self.name.mode: self.rca_view.update_viewer_mode})

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

    def _set_annotations_asset(self, annotations_asset_path: str) -> None:
        self.rca_view.set_annotations_asset(annotations_asset_path)

    def _load_eeg_files(
        self, eeg_fileset: EEGFileset, annotations_file: AnnotationsFile | None, is_new_eeg_fileset: bool
    ) -> None:
        try:
            if is_new_eeg_fileset or self._current_tmpdir is None:
                self._create_tmp_dir()

            eeg_assets: tuple[Asset, Asset] = self.ctrl.download_eeg_files(
                eeg_fileset,
                self._current_tmpdir.name,
                annotations_file=annotations_file,
            )
            eeg_asset, annotations_asset = eeg_assets

            if not is_eeg_file(eeg_asset):
                raise FileValidationError(f"EEG file {eeg_asset.name} is invalid")

            if not is_annotations_file(annotations_asset):
                raise FileValidationError(f"Annotation file {annotations_asset.name} is invalid")

            self.data.eeg_asset = eeg_asset
            self.data.annotations_asset = annotations_asset

            if is_new_eeg_fileset:
                self._set_files(self.data.eeg_asset.path)
            self._set_annotations_asset(self.data.annotations_asset.path)

        except DatabaseError as e:
            if annotations_file is None:
                raise EEGViewerError(f"Could not download file: {eeg_fileset.name}") from e
            raise EEGViewerError(
                f"Could not download files into annotator: ({eeg_fileset.name}, {annotations_file.name})"
            ) from e

        except (FileNotFoundError, FileValidationError, RCAViewError) as e:
            if annotations_file is None:
                raise EEGViewerError(f"Could not load file into viewer: {eeg_fileset.name}") from e
            raise EEGViewerError(
                f"Could not load files into viewer: ({eeg_fileset.name}, {annotations_file.name})"
            ) from e

    def load_eeg_files(
        self,
        eeg_fileset: EEGFileset,
        annotations_file: AnnotationsFile | None,
        is_new_eeg_fileset: bool,
    ) -> Task:
        async def _load() -> None:
            try:
                updated_eeg_fileset: EEGFileset = self.ctrl.refresh_eeg_fileset(eeg_fileset, compute_eeg=True)

                await to_thread(self._load_eeg_files, updated_eeg_fileset, annotations_file, is_new_eeg_fileset)

                readonly = updated_eeg_fileset.is_validated
                if not readonly and annotations_file is not None:
                    readonly = not (
                        annotations_file.status == AnnotationStatus.IN_PROGRESS
                        and annotations_file.author._id == self.current_user.data._id
                    )

                self.data.load_status = LoadStatus.LOADED
                self.data.mode = RCAViewMode.READONLY if readonly else RCAViewMode.EDIT

            except EEGViewerError as e:
                self.data.load_status = LoadStatus.ERROR
                self.data.status_message = str(e)
                raise e

            return updated_eeg_fileset, annotations_file

        self.reset_state()
        self.data.load_status = LoadStatus.LOADING
        if self.task and not self.task.done():
            self.task.cancel()
        self.task = self.create_async_task(_load)
        return self.task

    def save_annotations_file(self, eeg_fileset: EEGFileset) -> AnnotationsFile:
        try:
            if self._current_tmpdir is None:
                raise RuntimeError("Temporary directory is not initialized")

            if eeg_fileset.is_validated:
                raise EEGViewerError(f"{eeg_fileset.name} do not accept any more annotations")

            annotations_asset = self.data.annotations_asset

            self.rca_view.save_annotations_asset(self.data.annotations_asset.path)

            annotations_file: AnnotationsFile = self.ctrl.upload_annotations_file(eeg_fileset, annotations_asset)
            return annotations_file

        except (FileNotFoundError, DatabaseError) as e:
            raise EEGViewerError(f"Could not save annotations on {eeg_fileset.name}") from e
