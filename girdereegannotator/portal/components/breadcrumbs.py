from dataclasses import dataclass

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal


@dataclass
class BreadcrumbsState:
    dataset_name: str | None = None
    eeg_name: str | None = None


class Breadcrumbs(html.Div):
    root_clicked = Signal()
    dataset_clicked = Signal()

    def __init__(self, breadcrumbs_state: TypedState[BreadcrumbsState], **kwargs):
        super().__init__(classes="d-flex align-center", style="gap: 8px", **kwargs)

        with self:
            self._build_breadcrumbs_button(
                active=f"!{breadcrumbs_state.name.dataset_name}",
                click=self.root_clicked,
                icon="mdi-home",
            )
            v3.VIcon(v_if=breadcrumbs_state.name.dataset_name, disabled=True, icon="mdi-chevron-right")
            self._build_breadcrumbs_button(
                v_if=breadcrumbs_state.name.dataset_name,
                active=f"!{breadcrumbs_state.name.eeg_name}",
                click=self.dataset_clicked,
                text=(breadcrumbs_state.name.dataset_name,),
            )
            v3.VIcon(v_if=breadcrumbs_state.name.eeg_name, disabled=True, icon="mdi-chevron-right")
            self._build_breadcrumbs_button(
                v_if=breadcrumbs_state.name.eeg_name,
                text=(breadcrumbs_state.name.eeg_name,),
            )

    def _build_breadcrumbs_button(self, active: str | bool = True, **kwargs) -> None:
        active = str(active).lower() if isinstance(active, bool) else active
        active_color = (f"{active} ? 'primary' : 'undefined'",)
        active = (active,)

        v3.VBtn(
            classes="pa-0",
            variant="plain",
            density="compact",
            readonly=active,
            active=active,
            active_color=active_color,
            ripple=False,
            **kwargs,
        )
