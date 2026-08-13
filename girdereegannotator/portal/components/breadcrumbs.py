from dataclasses import dataclass, field
from enum import Enum, auto

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import BIDSDataset, EEGFileset


class BreadcrumbsElement(Enum):
    ROOT = auto()
    DATASET = auto()


@dataclass
class BreadcrumbsState:
    dataset: BIDSDataset = field(default_factory=BIDSDataset)
    eeg_fileset: EEGFileset = field(default_factory=EEGFileset)


class Breadcrumbs(html.Div):
    breadcrumbs_clicked = Signal(BreadcrumbsElement)

    def __init__(self, breadcrumbs_state: TypedState[BreadcrumbsState], **kwargs):
        super().__init__(classes="button-bar", **kwargs)

        with self:
            self._build_breadcrumbs_button(
                active=f"!{breadcrumbs_state.name.dataset.name}",
                click=(lambda: self.breadcrumbs_clicked(BreadcrumbsElement.ROOT)),
                icon="mdi-home",
            )
            v3.VIcon(v_if=breadcrumbs_state.name.dataset.name, disabled=True, icon="mdi-chevron-right")
            self._build_breadcrumbs_button(
                v_if=breadcrumbs_state.name.dataset.name,
                active=f"!{breadcrumbs_state.name.eeg_fileset.name}",
                click=(lambda: self.breadcrumbs_clicked(BreadcrumbsElement.DATASET)),
                text=(breadcrumbs_state.name.dataset.name,),
            )
            v3.VIcon(v_if=breadcrumbs_state.name.eeg_fileset.name, disabled=True, icon="mdi-chevron-right")
            self._build_breadcrumbs_button(
                v_if=breadcrumbs_state.name.eeg_fileset.name,
                text=(breadcrumbs_state.name.eeg_fileset.name,),
            )

    def _build_breadcrumbs_button(self, active: str | bool = True, **kwargs) -> None:
        active = str(active).lower() if isinstance(active, bool) else active
        active_color = (f"{active} ? 'primary' : 'undefined'",)
        active = (active,)

        v3.VBtn(
            classes="breadcrumbs-button",
            variant="plain",
            density="compact",
            readonly=active,
            active=active,
            active_color=active_color,
            ripple=False,
            **kwargs,
        )
