import tempfile
from asyncio import Task
from collections.abc import Callable
from inspect import iscoroutinefunction
from pathlib import Path

from trame_rca.utils import RcaViewAdapter
from trame_server import Server
from trame_server.utils.asynchronous import create_task
from trame_server.utils.typed_state import TypedState

from girdereegannotator.database.models import Asset, BIDSExtension, EEGMedia

from .components import RCAView
from .eeg_viewer_ui import EEGViewerState, EEGViewerUI, LoadStatus


class FileValidationError(Exception):
    pass


class AnnotatorLoadingError(Exception):
    pass


def is_eeg_file(file: Asset) -> bool:
    return file.name.endswith(BIDSExtension.eeg)


def is_annotation_file(file: Asset) -> bool:
    return file.name.endswith(BIDSExtension.annotation)


class AsyncTracker:
    def __init__(
        self,
        server: Server,
    ) -> None:
        self.server = server.root_server
        self.state = server.state

    async def __aenter__(self) -> None:
        self.state.flush()
        await self.server.network_completion

    async def __aexit__(self, *_args) -> None:
        self.state.flush()
        await self.server.network_completion


def create_async_task(
    tracker: AsyncTracker,
    callable_method: Callable[..., None],
    *args,
) -> Task:
    async def async_task() -> None:
        async with tracker:
            if iscoroutinefunction(callable_method):
                await callable_method(*args)
            else:
                callable_method(*args)

    return create_task(async_task())


class EEGViewerLogic:
    view_handler: RcaViewAdapter

    def __init__(self, server: Server):
        self.server = server
        self.rca_view = RCAView()
        self.typed_state = TypedState(self.server.state, EEGViewerState)
        self._current_tmpdir: tempfile.TemporaryDirectory[str] | None = None
        self.task: Task | None = None

        self.load_tracker = AsyncTracker(server)

    @property
    def name(self) -> EEGViewerState:
        return self.typed_state.name

    @property
    def data(self) -> EEGViewerState:
        return self.typed_state.data

    def set_ui(self, ui: EEGViewerUI) -> None:
        self.view_handler = ui.rca.create_view_handler(self.rca_view)

    def reset_state(self) -> None:
        self.typed_state.set_dataclass(EEGViewerState())

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

    def _load_eeg_media_files(self, eeg_media: EEGMedia) -> None:
        self._create_tmp_dir()

        eeg_media_files: tuple[Asset, Asset] = self.server.controller.download_eeg_media_files(
            eeg_media,
            self._current_tmpdir.name,
            annotation_file=eeg_media.annotations[0] if eeg_media.annotations else None,
        )
        eeg_file, annotation_file = eeg_media_files

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

    def load_eeg_media_files(self, eeg_media: EEGMedia) -> None:
        def _load() -> None:
            try:
                self._load_eeg_media_files(eeg_media)
                self.data.load_status = LoadStatus.LOADED

            except (FileValidationError, AnnotatorLoadingError) as e:
                self.data.load_status = LoadStatus.ERROR
                self.data.status_message = str(e)
                raise e

        self.reset_state()
        self.data.load_status = LoadStatus.LOADING
        if self.task and not self.task.done():
            self.task.cancel()
        self.task = create_async_task(self.load_tracker, _load)

    def save_annotations(self, eeg_media: EEGMedia) -> None:
        if self._current_tmpdir is None:
            raise RuntimeError("Temporary directory is not initialized")

        annotation_file = self.data.annotation_file

        if annotation_file.path is None or not Path(annotation_file.path).exists():
            raise FileNotFoundError(f"Annotation file ({annotation_file.path}) does not exist")

        annotation_file = self.server.controller.save_annotations(eeg_media, annotation_file)
        eeg_media.annotations.append(annotation_file)
