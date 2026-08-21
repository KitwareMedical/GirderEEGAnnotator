from enum import Enum, auto

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import Dataset, EEGFileset


class BreadcrumbsElement(Enum):
    ROOT = auto()
    DATASET = auto()


class Breadcrumbs(html.Div):
    breadcrumbs_clicked = Signal(BreadcrumbsElement)

    def __init__(self, dataset_state: TypedState[Dataset], eeg_fileset_state: TypedState[EEGFileset], **kwargs):
        super().__init__(classes="button-bar", **kwargs)

        with self:
            self._build_breadcrumbs_button(
                active=f"!{dataset_state.name.name}",
                click=(lambda: self.breadcrumbs_clicked(BreadcrumbsElement.ROOT)),
                icon="mdi-home",
            )
            v3.VIcon(v_if=dataset_state.name.name, disabled=True, icon="mdi-chevron-right")
            self._build_breadcrumbs_button(
                v_if=dataset_state.name.name,
                active=f"!{eeg_fileset_state.name.name}",
                click=(lambda: self.breadcrumbs_clicked(BreadcrumbsElement.DATASET)),
                text=(dataset_state.name.name,),
            )
            v3.VIcon(v_if=eeg_fileset_state.name.name, disabled=True, icon="mdi-chevron-right")
            self._build_breadcrumbs_button(
                v_if=eeg_fileset_state.name.name,
                text=(eeg_fileset_state.name.name,),
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
