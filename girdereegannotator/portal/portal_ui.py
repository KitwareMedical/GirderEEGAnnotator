from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3

from girdereegannotator.utils.base_ui import BaseUI

from .components.breadcrumbs import Breadcrumbs, BreadcrumbsState
from .components.dataset_list import DatasetList, DatasetListState
from .components.eeg_fileset_list import EEGFilesetList, EEGFilesetListState


@dataclass
class PortalState:
    breadcrumbs_state: BreadcrumbsState = field(default_factory=BreadcrumbsState)
    dataset_list_state: DatasetListState = field(default_factory=DatasetListState)
    eeg_fileset_list_state: EEGFilesetListState = field(default_factory=EEGFilesetListState)


class PortalPagination(html.Div):
    def __init__(self, **kwargs) -> None:
        super().__init__(classes="portal-pagination", **kwargs)

        with self:
            v3.VBtn(icon="mdi-chevron-left", variant="text")
            v3.VBtn(icon="mdi-chevron-right", variant="text")


class PortalUI(html.Div, BaseUI[PortalState]):
    def __init__(self, **kwargs) -> None:
        super().__init__(classes="portal", **kwargs)
        self._init_typed_state(self.state, PortalState)
        with self:
            with v3.VFadeTransition(mode="out-in"):
                self.dataset_list = DatasetList(
                    v_if=f"!{self.name.breadcrumbs_state.dataset.name}",
                    list_state=self.get_sub_state(self.name.dataset_list_state),
                )
                self.eeg_fileset_list = EEGFilesetList(
                    v_else_if=f"!{self.name.breadcrumbs_state.eeg_fileset.name}",
                    list_state=self.get_sub_state(self.name.eeg_fileset_list_state),
                )
            PortalPagination()

    def build_breadcrumbs(self, **kwargs) -> None:
        self.breadcrumbs_ui = Breadcrumbs(self.get_sub_state(self.name.breadcrumbs_state), **kwargs)
