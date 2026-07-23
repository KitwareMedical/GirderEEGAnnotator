from trame_server import Server
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import EEGMedia

from .portal_ui import PortalState


class PortalLogic:
    eeg_media_selected = Signal(EEGMedia | None)

    def __init__(self, server: Server) -> None:
        self.server = server
        self.typed_state = TypedState(self.server.state, PortalState)
        self.typed_state.bind_changes(
            {
                self.typed_state.name.eeg_media_index: self._select_eeg_media,
                self.typed_state.name.dataset_index: self._select_dataset,
            }
        )

    @property
    def name(self) -> PortalState:
        return self.typed_state.name

    @property
    def data(self) -> PortalState:
        return self.typed_state.data

    def _refresh_dataset_list(self) -> None:
        self.data.dataset_list = self.server.controller.list_datasets()

    def _refresh_eeg_list(self) -> None:
        if self.data.dataset_index is None:
            return
        self.data.eeg_media_list = self.server.controller.list_eeg_media(
            self.data.dataset_list[self.data.dataset_index]
        )

    def _select_dataset(self, dataset_index: int | None) -> None:
        if dataset_index is None:
            self.reset_state()

        self._refresh_eeg_list()

    def _select_eeg_media(self, eeg_media_index: int | None) -> None:
        self.eeg_media_selected(self.data.eeg_media_list[eeg_media_index] if eeg_media_index is not None else None)

    def reset_state(self) -> None:
        self.typed_state.set_dataclass(PortalState())
        self._refresh_dataset_list()

    def _shift_eeg_media_index(self, offset: int) -> None:
        if self.data.dataset_index is None or not self.data.eeg_media_list:
            return

        self.data.eeg_media_index = (self.data.eeg_media_index + offset) % len(self.data.eeg_media_list)

    def select_previous_eeg(self) -> None:
        self._shift_eeg_media_index(-1)

    def select_next_eeg(self) -> None:
        self._shift_eeg_media_index(1)

    def update_eeg_media_list(self, eeg_media: EEGMedia) -> None:
        self.data.eeg_media_list = [
            eeg_media if media.raw_eeg._id == eeg_media.raw_eeg._id else media for media in self.data.eeg_media_list
        ]
