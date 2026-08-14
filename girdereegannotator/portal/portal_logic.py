from trame_server import Server
from undo_stack import Signal

from girdereegannotator.database.models import EEGMedia
from girdereegannotator.utils.base_logic import BaseLogic

from .portal_ui import PortalState, PortalUI


class PortalLogic(BaseLogic[PortalState]):
    eeg_media_selected = Signal(EEGMedia | None)
    breadcrumbs_clicked = Signal()

    def __init__(self, server: Server) -> None:
        super().__init__(server, PortalState)
        self.bind_changes(
            {
                self.typed_state.name.eeg_media_index: self._on_eeg_media_selected,
                self.typed_state.name.dataset_index: self._on_dataset_selected,
            }
        )

    def _refresh_dataset_list(self) -> None:
        self.data.dataset_list = self.server.controller.list_datasets()

    def _refresh_eeg_list(self) -> None:
        if self.data.dataset_index is None:
            return

        self.data.eeg_media_list = self.server.controller.list_eeg_media(
            self.data.dataset_list[self.data.dataset_index]
        )

    def _on_root_clicked(self) -> None:
        self.data.dataset_index = None
        self.breadcrumbs_clicked()

    def _on_dataset_clicked(self) -> None:
        self.data.eeg_media_index = None
        self.breadcrumbs_clicked()

    def _on_dataset_selected(self, dataset_index: int | None) -> None:
        if dataset_index is None:
            self.data.eeg_media_list = []
            self.data.eeg_media_index = None
            self.data.breadcrumbs_state.dataset_name = None
            self._refresh_dataset_list()
            return

        self._refresh_eeg_list()
        self.data.breadcrumbs_state.dataset_name = self.data.dataset_list[dataset_index].name

    def _on_eeg_media_selected(self, eeg_media_index: int | None) -> None:
        if eeg_media_index is None:
            self.data.breadcrumbs_state.eeg_name = None
            self.eeg_media_selected(None)
            self._refresh_eeg_list()
            return

        eeg_media = self.data.eeg_media_list[eeg_media_index]
        self.data.breadcrumbs_state.eeg_name = eeg_media.name
        self.eeg_media_selected(eeg_media)

    def reset_state(self) -> None:
        super().reset_state()
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

    def set_ui(self, ui: PortalUI) -> None:
        ui.breadcrumbs_ui.root_clicked.connect(self._on_root_clicked)
        ui.breadcrumbs_ui.dataset_clicked.connect(self._on_dataset_clicked)
