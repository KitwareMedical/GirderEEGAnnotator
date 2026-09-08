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


def upsert_annotations_file(eeg_fileset: EEGFileset, new_annotations_file: AnnotationsFile) -> EEGFileset:
    if any(ann._id == new_annotations_file._id for ann in eeg_fileset.annotations_files):
        eeg_fileset.annotations_files = [
            new_annotations_file if ann._id == new_annotations_file._id else ann
            for ann in eeg_fileset.annotations_files
        ]
    else:
        eeg_fileset.annotations_files.append(new_annotations_file)
    return eeg_fileset


class EEGViewerLogic(BaseLogic[EEGViewerState]):
    view_handler: RcaViewAdapter

    def __init__(self, server: Server):
        super().__init__(server, EEGViewerState)
        self.rca_view = RCAView()
        self._current_tmpdir: tempfile.TemporaryDirectory[str] | None = None
        self.load_task: Task | None = None
        self.save_task: Task | None = None
        self.delete_task: Task | None = None

        self.current_user = TypedState(self.state, User)
        self.bind_changes({self.name.mode: self.rca_view.update_viewer_mode})

    def set_ui(self, ui: EEGViewerUI) -> None:
        self.view_handler = ui.rca.create_view_handler(self.rca_view)

    def set_readonly_mode(self) -> None:
        self.data.mode = RCAViewMode.READONLY

    def set_edit_mode(self) -> None:
        self.data.mode = RCAViewMode.EDIT

    def unset_mode(self) -> None:
        self.data.mode = RCAViewMode.UNDEFINED

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

    def _update_viewer_mode(
        self, current_eeg_fileset: EEGFileset, current_annotations_file: AnnotationsFile | None
    ) -> None:
        readonly = current_eeg_fileset.is_validated
        if not readonly and current_annotations_file is not None:
            readonly = not (
                current_annotations_file.status == AnnotationStatus.IN_PROGRESS
                and current_annotations_file.author._id == self.current_user.data._id
            )

        self.data.mode = RCAViewMode.READONLY if readonly else RCAViewMode.EDIT

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
        async def _load() -> tuple[EEGFileset, AnnotationsFile]:
            try:
                refreshed_eeg_fileset: EEGFileset = self.ctrl.refresh_eeg_fileset(eeg_fileset, compute_eeg=True)
                await to_thread(self._load_eeg_files, refreshed_eeg_fileset, annotations_file, is_new_eeg_fileset)

                self.data.load_status = LoadStatus.LOADED

                self._update_viewer_mode(refreshed_eeg_fileset, annotations_file)

                return refreshed_eeg_fileset, annotations_file

            except EEGViewerError as e:
                self.data.load_status = LoadStatus.ERROR
                self.data.status_message = str(e)
                raise e

        self.reset_state()
        self.data.load_status = LoadStatus.LOADING
        if self.load_task and not self.load_task.done():
            self.load_task.cancel()
        self.load_task = self.create_async_task(_load)
        return self.load_task

    def _save_annotations_file(self, eeg_fileset: EEGFileset) -> AnnotationsFile:
        try:
            if self._current_tmpdir is None:
                raise RuntimeError("Temporary directory is not initialized")

            if eeg_fileset.is_validated:
                raise EEGViewerError(f"{eeg_fileset.name} do not accept any more annotations")

            annotations_asset = self.data.annotations_asset

            self.rca_view.save_annotations_asset(self.data.annotations_asset.path)

            return self.ctrl.upload_annotations_file(eeg_fileset, annotations_asset)

        except (RuntimeError, FileNotFoundError, DatabaseError) as e:
            raise EEGViewerError(f"Could not save annotations on {eeg_fileset.name}") from e

    def _update_annotations_status(self, annotations_file: AnnotationsFile) -> None:
        try:
            self.ctrl.update_annotations_file_status(annotations_file)
        except DatabaseError as e:
            raise EEGViewerError(
                f"Could not update {annotations_file.name} status to {annotations_file.status.value}"
            ) from e

    def save_annotations_file(
        self, eeg_fileset: EEGFileset, annotations_file: AnnotationsFile, annotation_status: AnnotationStatus | None
    ) -> Task:
        async def _save() -> tuple[EEGFileset, AnnotationsFile]:
            try:
                refreshed_eeg_fileset: EEGFileset = self.ctrl.refresh_eeg_fileset(eeg_fileset, compute_eeg=True)
                if annotations_file.status == AnnotationStatus.IN_PROGRESS:
                    updated_annotations_file = await to_thread(self._save_annotations_file, refreshed_eeg_fileset)
                else:
                    updated_annotations_file = annotations_file

                if annotation_status is not None:
                    updated_annotations_file.status = annotation_status
                    self._update_annotations_status(updated_annotations_file)

                updated_eeg_fileset = upsert_annotations_file(refreshed_eeg_fileset, updated_annotations_file)

                self._update_viewer_mode(updated_eeg_fileset, updated_annotations_file)

                return updated_eeg_fileset, updated_annotations_file

            except EEGViewerError as e:
                raise e

        if self.save_task and not self.save_task.done():
            self.save_task.cancel()
        self.save_task = self.create_async_task(_save)
        return self.save_task

    def _delete_annotations_file(self, annotations_file: AnnotationsFile) -> None:
        try:
            self.ctrl.delete_annotations_file(annotations_file)
        except DatabaseError as e:
            raise EEGViewerError(f"Could not delete {annotations_file.name}") from e

    def delete_annotations_file(self, eeg_fileset: EEGFileset, annotations_file: AnnotationsFile) -> Task:
        async def _delete() -> tuple[EEGFileset, AnnotationsFile]:
            try:
                await to_thread(self._delete_annotations_file, annotations_file)
                updated_eeg_fileset: EEGFileset = self.ctrl.refresh_eeg_fileset(eeg_fileset, compute_eeg=True)
                updated_annotations_file = None

                # Update viewer with new annotation
                await to_thread(self._load_eeg_files, updated_eeg_fileset, updated_annotations_file, False)

                self._update_viewer_mode(updated_eeg_fileset, None)

                return updated_eeg_fileset, None

            except EEGViewerError as e:
                raise e

        if self.delete_task and not self.delete_task.done():
            self.delete_task.cancel()
        self.delete_task = self.create_async_task(_delete)
        return self.delete_task
