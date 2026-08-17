from trame_server import Server
from undo_stack import Signal

from girdereegannotator.database.models import BIDSDataset, EEGFileset
from girdereegannotator.utils.base_logic import BaseLogic

from .components.breadcrumbs import BreadcrumbsElement
from .portal_ui import PortalState, PortalUI


class PortalLogic(BaseLogic[PortalState]):
    eeg_fileset_selected = Signal(EEGFileset | None)
    eeg_fileset_unselected = Signal()
    select_eeg_fileset = Signal(int)

    def __init__(self, server: Server) -> None:
        super().__init__(server, PortalState)
        self.current_dataset = self.get_sub_state(self.name.current_dataset)
        self.current_eeg_fileset = self.get_sub_state(self.name.current_eeg_fileset)

    def _refresh_dataset_list(self) -> None:
        self.data.dataset_list_state.items = self.server.controller.list_datasets()

    def _refresh_eeg_list(self) -> None:
        if self.current_dataset.data._id is None:
            self.data.eeg_fileset_list_state.items = []
            self.data.eeg_fileset_list_state.current_index = None
            return

        self.data.eeg_fileset_list_state.items = self.server.controller.list_eeg_filesets(
            self.current_dataset.get_dataclass()
        )

    def reset_dataset(self) -> None:
        self.current_dataset.set_dataclass(BIDSDataset())
        self._reset_eeg_fileset()
        self._refresh_dataset_list()

    def _reset_eeg_fileset(self) -> None:
        self.current_eeg_fileset.set_dataclass(EEGFileset())
        self._refresh_eeg_list()
        self.eeg_fileset_unselected()

    def _on_breadcrumbs_clicked(self, breadcrumbs_element: BreadcrumbsElement) -> None:
        if breadcrumbs_element == BreadcrumbsElement.ROOT:
            self.reset_dataset()

        elif breadcrumbs_element == BreadcrumbsElement.DATASET:
            self._reset_eeg_fileset()

    def _on_dataset_selected(self, dataset: BIDSDataset) -> None:
        self.current_dataset.set_dataclass(dataset)
        self._refresh_eeg_list()

    def _on_eeg_fileset_selected(self, eeg_fileset: EEGFileset) -> None:
        self.current_eeg_fileset.set_dataclass(eeg_fileset)
        self.eeg_fileset_selected(eeg_fileset)

    def _shift_eeg_fileset_index(self, offset: int) -> None:
        if self.data.eeg_fileset_list_state.current_index is None or not self.data.eeg_fileset_list_state.items:
            return
        self.select_eeg_fileset(
            (self.data.eeg_fileset_list_state.current_index + offset) % len(self.data.eeg_fileset_list_state.items)
        )

    def select_previous_eeg(self) -> None:
        self._shift_eeg_fileset_index(-1)

    def select_next_eeg(self) -> None:
        self._shift_eeg_fileset_index(1)

    def update_eeg_fileset_list(self, eeg_fileset: EEGFileset) -> None:
        self.current_eeg_fileset.set_dataclass(eeg_fileset)
        self.data.eeg_fileset_list_state.items = [
            eeg_fileset if index == self.data.eeg_fileset_list_state.current_index else media
            for (index, media) in enumerate(self.data.eeg_fileset_list_state.items)
        ]

    def set_ui(self, ui: PortalUI) -> None:
        ui.breadcrumbs_ui.breadcrumbs_clicked.connect(self._on_breadcrumbs_clicked)
        ui.dataset_list.item_selected.connect(self._on_dataset_selected)
        ui.eeg_fileset_list.item_selected.connect(self._on_eeg_fileset_selected)

        self.select_eeg_fileset.connect(ui.eeg_fileset_list.select_item)
