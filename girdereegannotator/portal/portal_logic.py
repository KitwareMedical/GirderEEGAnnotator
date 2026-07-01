from trame_server import Server
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import EEGMedia, EEGMediaFile

from .loader_logic import LoaderLogic
from .portal_ui import PortalState, PortalUI

ANNOTATION_FILE_SUFFIX = "annotations.csv"
EEG_FILE_EXTENSIONS = (".neonatal", ".edf")


class FileValidationError(Exception):
    pass


class AnnotatorLoadingError(Exception):
    pass


def are_eeg_files(files: list[EEGMediaFile]) -> bool:
    return len(files) <= 2 and any(file.name.endswith(EEG_FILE_EXTENSIONS) for file in files)


class PortalLogic:
    eeg_media_selected = Signal()

    def __init__(self, server: Server) -> None:
        self.server = server
        self.typed_state = TypedState(self.server.state, PortalState)
        self._current_eeg_media = self.typed_state.get_sub_state(self.typed_state.name.eeg_media)

        self.loader_logic = LoaderLogic(server)

    @property
    def name(self) -> PortalState:
        return self.typed_state.name

    @property
    def data(self) -> PortalState:
        return self.typed_state.data

    def reset_state(self) -> None:
        self.typed_state.set_dataclass(PortalState())

    def _get_eeg_media_index(self) -> int:
        return next((i for i, item in enumerate(self.data.eeg_media_list) if item._id == self.data.eeg_media._id), None)

    def set_eeg_media_list(self) -> None:
        self.data.eeg_media_list = self.server.controller.list_eeg_media()

    def set_ui(self, ui: PortalUI) -> None:
        ui.eeg_media_selected.connect(self._on_eeg_media_selected)
        ui.save_annotations_clicked.connect(self._save_eeg_annotations)
        ui.previous_eeg_clicked.connect(self._select_previous_media)
        ui.next_eeg_clicked.connect(self._select_next_media)

    def _on_eeg_media_selected(self, eeg_media: EEGMedia) -> None:
        self._set_current_eeg_media(eeg_media)
        self.loader_logic.load_eeg_media_files(eeg_media._id)

    def _set_current_eeg_media(self, eeg_media: EEGMedia, update_media_list: bool = False) -> None:
        self._current_eeg_media.set_dataclass(eeg_media)
        if update_media_list:
            self.data.eeg_media_list = [
                eeg_media if eeg_media._id == media._id else media for media in self.data.eeg_media_list
            ]
        self.eeg_media_selected()

    def _save_eeg_annotations(self) -> None:
        eeg_media = self.loader_logic.save_eeg_annotations(self._current_eeg_media.data._id)
        self._set_current_eeg_media(eeg_media, update_media_list=True)

    def _select_next_media(self) -> None:
        if len(self.data.eeg_media_list) == 0:
            return

        eeg_media_index = self._get_eeg_media_index()
        if eeg_media_index == (len(self.data.eeg_media_list) - 1) or eeg_media_index is None:
            next_index = 0
        else:
            next_index = eeg_media_index + 1
        self._set_current_eeg_media(self.data.eeg_media_list[next_index])

    def _select_previous_media(self) -> None:
        if len(self.data.eeg_media_list) == 0:
            return

        eeg_media_index = self._get_eeg_media_index()
        if eeg_media_index == 0:
            previous_index = len(self.data.eeg_media_list) - 1
        elif eeg_media_index is None:
            previous_index = 0
        else:
            previous_index = eeg_media_index - 1
        self._set_current_eeg_media(self.data.eeg_media_list[previous_index])
