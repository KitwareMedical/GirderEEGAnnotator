import tempfile
from collections.abc import Callable
from inspect import iscoroutinefunction
from pathlib import Path
from typing import Any

from trame_server import Server
from trame_server.utils.asynchronous import create_task
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import EEGMedia, EEGMediaFile

from .portal_ui import LoaderState

ANNOTATION_FILE_SUFFIX = "annotations.csv"
EEG_FILE_EXTENSIONS = (".neonatal", ".edf")


class FileValidationError(Exception):
    pass


class AnnotatorLoadingError(Exception):
    pass


def are_eeg_files(files: list[EEGMediaFile]) -> bool:
    return len(files) <= 2 and any(file.name.endswith(EEG_FILE_EXTENSIONS) for file in files)


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
) -> None:
    async def async_task() -> None:
        async with tracker:
            if iscoroutinefunction(callable_method):
                await callable_method(*args)
            else:
                callable_method(*args)

    create_task(async_task())


class LoaderLogic:
    eeg_media_loaded = Signal(str)

    def __init__(self, server: Server):
        self.server = server
        self.typed_state = TypedState(self.server.state, LoaderState)
        self._current_tmpdir: tempfile.TemporaryDirectory[str] | None = None

        self.load_tracker = AsyncTracker(server, self.name.eeg_loading)

    @property
    def name(self) -> LoaderState:
        return self.typed_state.name

    @property
    def data(self) -> LoaderState:
        return self.typed_state.data

    def _cleanup_current_tmpdir(self) -> None:
        if self._current_tmpdir is not None:
            self._current_tmpdir.cleanup()
            self._current_tmpdir = None

    def _create_tmp_dir(self) -> None:
        self._cleanup_current_tmpdir()
        self._current_tmpdir = tempfile.TemporaryDirectory()

    def _format_eeg_files(self, eeg_media_files: list[EEGMediaFile]) -> None:
        eeg_media_files.sort(key=lambda d: d.name)
        self.data.eeg_file = eeg_media_files[0]

        annotation_file_name = f"{self.data.eeg_file.name}.{ANNOTATION_FILE_SUFFIX}"
        annotation_file_path = Path(self._current_tmpdir.name) / annotation_file_name
        has_annotation_file = len(eeg_media_files) == 2 and eeg_media_files[1].name == annotation_file_name

        self.data.eeg_annotation_file = (
            eeg_media_files[1]
            if has_annotation_file
            else EEGMediaFile(
                name=annotation_file_name,
                path=str(annotation_file_path),
            )
        )

    def _load_eeg_media_files(self, eeg_media_id: str) -> None:
        self._create_tmp_dir()

        eeg_media_files: list[EEGMediaFile] = self.server.controller.download_eeg_media_files(
            eeg_media_id, self._current_tmpdir.name
        )

        if len(eeg_media_files) == 0:
            raise FileValidationError("No EEG files to load")

        if not are_eeg_files(eeg_media_files):
            raise FileValidationError("EEG files are invalid")

        self._format_eeg_files(eeg_media_files)

        try:
            self.eeg_media_loaded(self.data.eeg_file.path)
        except Exception as e:
            raise AnnotatorLoadingError(f"Could not load data into EEG Annotator: {e}") from e

    def _reset_state(self) -> None:
        self.data.eeg_file = None
        self.data.eeg_annotation_file = None

    def load_eeg_media_files(self, eeg_media_id: str) -> None:
        def _load() -> None:
            try:
                self._load_eeg_media_files(eeg_media_id)

            except FileValidationError:
                self._reset_state()
                raise

            except AnnotatorLoadingError:
                self._reset_state()
                raise

        create_async_task(self.load_tracker, _load)

    def save_eeg_annotations(self, eeg_media_id: str) -> EEGMedia:
        if self._current_tmpdir is None:
            raise RuntimeError("Temporary directory is not initialized")

        annotation_file = self.data.eeg_annotation_file

        if annotation_file is None:
            raise RuntimeError("Annotation file is missing")

        if not Path(annotation_file.path).exists():
            raise FileNotFoundError(f"Annotation file does not exist: {annotation_file.path}")

        return self.server.controller.save_eeg_annotations(eeg_media_id, annotation_file)
