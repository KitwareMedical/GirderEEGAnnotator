from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from undo_stack import Signal

from girdereegannotator.database.models import Dataset, EEGFileset
from girdereegannotator.utils.base_ui import BaseUI
from girdereegannotator.utils.components import Button

from .components.breadcrumbs import Breadcrumbs, BreadcrumbsElement
from .components.dataset_filters import DatasetFilters
from .components.dataset_list import DatasetList, DatasetListState
from .components.eeg_fileset_filters import EEGFilesetFilters, EEGFilesetFiltersState
from .components.eeg_fileset_list import EEGFilesetList, EEGFilesetListState
from .components.filters.search_filter import SearchState


@dataclass
class PortalState:
    me: str | None = None
    current_breadcrumbs_element: BreadcrumbsElement = BreadcrumbsElement.ROOT
    current_dataset: Dataset = field(default_factory=Dataset)
    current_eeg_fileset: EEGFileset = field(default_factory=EEGFileset)
    dataset_list_state: DatasetListState = field(default_factory=DatasetListState)
    eeg_fileset_list_state: EEGFilesetListState = field(default_factory=EEGFilesetListState)
    dataset_filter_state: SearchState = field(default_factory=SearchState)
    eeg_fileset_filter_state: EEGFilesetFiltersState = field(default_factory=EEGFilesetFiltersState)


class PortalUI(html.Div, BaseUI[PortalState]):
    refresh_clicked = Signal()

    def __init__(self, **kwargs) -> None:
        super().__init__(classes="portal", **kwargs)
        self._init_typed_state(self.state, PortalState)

        with self, v3.VFadeTransition(mode="out-in"):
            with html.Div(
                v_if=f"{self.name.current_breadcrumbs_element} == {BreadcrumbsElement.ROOT.value}",
                classes="fill-height",
            ):
                self.dataset_filters = DatasetFilters(filter_state=self.get_sub_state(self.name.dataset_filter_state))
                self.dataset_list = DatasetList(
                    item_state=self.get_sub_state(self.name.current_dataset),
                    list_state=self.get_sub_state(self.name.dataset_list_state),
                )

            with html.Div(
                v_else_if=f"{self.name.current_breadcrumbs_element} == {BreadcrumbsElement.DATASET.value}",
                classes="fill-height",
            ):
                self.eeg_fileset_filters = EEGFilesetFilters(
                    filter_state=self.get_sub_state(self.name.eeg_fileset_filter_state)
                )
                self.eeg_fileset_list = EEGFilesetList(
                    user_id=self.name.me,
                    item_state=self.get_sub_state(self.name.current_eeg_fileset),
                    list_state=self.get_sub_state(self.name.eeg_fileset_list_state),
                )

    def build_breadcrumbs(self, **kwargs) -> None:
        self.breadcrumbs_ui = Breadcrumbs(
            current_breadcrumbs_element=self.name.current_breadcrumbs_element,
            dataset_name=self.name.current_dataset.name,
            eeg_fileset_name=self.name.current_eeg_fileset.name,
            **kwargs,
        )

    def build_toolbar(self) -> None:
        Button(
            click=self.refresh_clicked,
            icon="mdi-refresh",
            tooltip="Refresh list",
        )
