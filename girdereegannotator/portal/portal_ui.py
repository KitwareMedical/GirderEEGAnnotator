from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import BIDSDataset, EEGFileset
from girdereegannotator.utils.base_ui import BaseUI

from .components.breadcrumbs import Breadcrumbs, BreadcrumbsState


@dataclass
class PortalState:
    breadcrumbs_state: BreadcrumbsState = field(default_factory=BreadcrumbsState)
    dataset_index: int | None = None
    dataset_list: list[BIDSDataset] = field(default_factory=list)
    eeg_fileset_index: int | None = None
    eeg_fileset_list: list[EEGFileset] = field(default_factory=list)


class PortalList(v3.VList):
    def __init__(self, **kwargs):
        super().__init__(classes="portal-list", variant="tonal", **kwargs)


class PortalListItem(v3.VListItem):
    def __init__(self, **kwargs):
        super().__init__(classes="portal-list-item", rounded=True, **kwargs)


class PortalEEGList(PortalList):
    send_to_viewer_clicked = Signal(int)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.typed_state = TypedState(self.state, PortalState)

        with (
            self,
            PortalListItem(
                v_for=f"(eeg_fileset, index) in {self.typed_state.name.eeg_fileset_list}",
                title=("eeg_fileset.name",),
                click=f"{self.typed_state.name.eeg_fileset_index} = index",  # enables to highlight item when hovered
            ),
            v3.Template(v_slot_append=True),
        ):
            v3.VChip(
                v_if="eeg_fileset.annotations.length",
                append_icon="mdi-tag",
                text=("eeg_fileset.annotations.length",),
                color="warning",
            )


class PortalPagination(html.Div):
    def __init__(self, **kwargs) -> None:
        super().__init__(classes="portal-pagination", **kwargs)

        with self:
            v3.VBtn(icon="mdi-chevron-left", variant="text")
            v3.VBtn(icon="mdi-chevron-right", variant="text")


class PortalDatasetList(PortalList):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.typed_state = TypedState(self.state, PortalState)
        with self:
            PortalListItem(
                v_for=f"(dataset, index) in {self.typed_state.name.dataset_list}",
                title=("dataset.name",),
                click=f"{self.typed_state.name.dataset_index} = index",
            )


class PortalUI(html.Div, BaseUI[PortalState]):
    def __init__(self, **kwargs) -> None:
        super().__init__(classes="portal", **kwargs)
        self._init_typed_state(self.state, PortalState)
        with self:
            with v3.VFadeTransition(mode="out-in"):
                PortalDatasetList(v_if=f"{self.name.dataset_index} == null")
                PortalEEGList(v_else=True)
            PortalPagination()

    def build_breadcrumbs(self, **kwargs) -> None:
        self.breadcrumbs_ui = Breadcrumbs(self.get_sub_state(self.name.breadcrumbs_state), **kwargs)
