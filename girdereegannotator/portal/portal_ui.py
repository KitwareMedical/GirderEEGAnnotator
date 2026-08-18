from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from undo_stack import Signal

from girdereegannotator.database.models import BIDSDataset, EEGFileset
from girdereegannotator.portal.components.expandable_list import ExpandableListState
from girdereegannotator.utils.base_ui import BaseUI
from girdereegannotator.utils.components import Button
from girdereegannotator.utils.load_status import (
    LoadErrorMessage,
    LoadProgress,
    LoadStatus,
)

from .components.breadcrumbs import Breadcrumbs
from .components.dataset_list import DatasetList, DatasetListState
from .components.eeg_fileset_list import EEGFilesetList, EEGFilesetListState


@dataclass
class PortalState:
    load_status: LoadStatus = LoadStatus.UNDEFINED
    status_message: str | None = None
    current_dataset: BIDSDataset = field(default_factory=BIDSDataset)
    current_eeg_fileset: EEGFileset = field(default_factory=EEGFileset)
    dataset_list_state: DatasetListState = field(default_factory=DatasetListState)
    eeg_fileset_list_state: EEGFilesetListState = field(default_factory=EEGFilesetListState)


class PortalUI(html.Div, BaseUI[PortalState]):
    refresh_clicked = Signal()

    def __init__(self, **kwargs) -> None:
        super().__init__(classes="portal", **kwargs)
        self._init_typed_state(self.state, PortalState)
        with self:
            with html.Div(style="height: 5px;"):
                LoadProgress(v_if=self.is_load_status(LoadStatus.LOADING))
            with html.Div(style="height: calc(100% - 5px);"), v3.VFadeTransition(mode="out-in"):
                LoadErrorMessage(
                    v_if=f"{self.is_load_status(LoadStatus.ERROR)} && {self.name.status_message} != null",
                    status_message=self.name.status_message,
                )
                self.dataset_list = DatasetList(
                    v_else_if=f"{self.is_list_showing(self.name.dataset_list_state)} && !{self.name.current_dataset.name}",
                    list_state=self.get_sub_state(self.name.dataset_list_state),
                )
                self.eeg_fileset_list = EEGFilesetList(
                    v_else_if=f"{self.is_list_showing(self.name.eeg_fileset_list_state)} && !{self.name.current_eeg_fileset.name}",
                    list_state=self.get_sub_state(self.name.eeg_fileset_list_state),
                )

    def build_breadcrumbs(self, **kwargs) -> None:
        self.breadcrumbs_ui = Breadcrumbs(
            dataset_state=self.get_sub_state(self.name.current_dataset),
            eeg_fileset_state=self.get_sub_state(self.name.current_eeg_fileset),
            **kwargs,
        )

    def build_toolbar(self) -> None:
        Button(
            v_if=f"!{self.name.current_eeg_fileset.name}",
            click=self.refresh_clicked,
            disabled=(self.is_load_status(LoadStatus.LOADING),),
            icon="mdi-refresh",
            tooltip="Refresh list",
        )

    def is_load_status(self, load_status: LoadStatus) -> str:
        return f"({self.name.load_status} == {load_status.value})"

    def is_list_showing(self, list_state: ExpandableListState) -> str:
        return (
            f"({self.is_load_status(LoadStatus.UNDEFINED)} || "
            f"({self.is_load_status(LoadStatus.LOADING)} && {list_state.items}.length))"
        )
