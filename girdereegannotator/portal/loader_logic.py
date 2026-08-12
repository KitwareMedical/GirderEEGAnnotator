import tempfile
from asyncio import Task
from collections.abc import Callable
from inspect import iscoroutinefunction
from pathlib import Path
from typing import Any

from trame_server import Server
from trame_server.utils.asynchronous import create_task
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import Asset, BIDSExtension, EEGMedia

from .loader_ui import LoaderState


class FileValidationError(Exception):
    pass


class AnnotatorLoadingError(Exception):
    pass


def is_eeg_file(file: Asset) -> bool:
    return file.name.endswith(BIDSExtension.eeg)


def is_annotation_file(file: Asset) -> bool:
    return file.name.endswith(BIDSExtension.annotation)


class AsyncTracker:
    def __init__(self, server: Server, loading_key: str) -> None:
        self.loading_key = loading_key
        self.server = server.root_server
        self.state = server.state

    @property
    def loading(self) -> Any:
        return self.state[self.loading_key]

    @loading.setter
    def loading(self, value: bool) -> None:
        self.state[self.loading_key] = value

    async def __aenter__(self) -> None:
        with self.state:
            self.loading = True
        await self.server.network_completion

    async def __aexit__(self, *_args) -> None:
        with self.state:
            self.loading = False
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


class LoaderLogic:
    eeg_media_downloaded = Signal(str, str)
    eeg_media_loaded = Signal()

    def __init__(self, server: Server):
        self.server = server
        self.typed_state = TypedState(self.server.state, LoaderState)
        self._current_tmpdir: tempfile.TemporaryDirectory[str] | None = None
        self.task: Task | None = None

        self.load_tracker = AsyncTracker(server, self.name.eeg_loading)

    @property
    def name(self) -> LoaderState:
        return self.typed_state.name

    @property
    def data(self) -> LoaderState:
        return self.typed_state.data

    def _reset_state(self) -> None:
        self.typed_state.set_dataclass(LoaderState())

    def _cleanup_current_tmpdir(self) -> None:
        if self._current_tmpdir is not None:
            self._current_tmpdir.cleanup()
            self._current_tmpdir = None

    def _create_tmp_dir(self) -> None:
        self._cleanup_current_tmpdir()
        self._current_tmpdir = tempfile.TemporaryDirectory()

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
            self.eeg_media_downloaded(self.data.eeg_file.path, self.data.annotation_file.path)
        except Exception as e:
            raise AnnotatorLoadingError(f"Could not load file into annotator: {e}") from e

    def load_eeg_media_files(self, eeg_media: EEGMedia) -> None:
        def _load() -> None:
            try:
                self._load_eeg_media_files(eeg_media)
                self.eeg_media_loaded()

            except (FileValidationError, AnnotatorLoadingError) as e:
                self.typed_state.data.load_error = str(e)
                raise e

        self._reset_state()
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
