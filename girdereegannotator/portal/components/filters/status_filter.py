from dataclasses import dataclass, field
from enum import Enum

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.utils.components import Button


class Status(Enum):
    UNDEFINED = "Show all"
    VALIDATED = "Validated"
    TO_VALIDATE = "To validate"
    TO_ANNOTATE = "To annotate"


@dataclass
class StatusState:
    status: Status = Status.UNDEFINED
    counts: dict[Status, int] = field(default_factory=dict)


class StatusFilter(v3.VBtnToggle):
    def __init__(self, status_state: TypedState[StatusState], on_status_clicked: Signal, **kwargs):
        super().__init__(v_model=status_state.name.status, **kwargs)

        status_buttons = [
            {"status": Status.UNDEFINED.value, "color": "undefined"},
            {"status": Status.VALIDATED.value, "color": "success"},
            {"status": Status.TO_VALIDATE.value, "color": "primary"},
            {"status": Status.TO_ANNOTATE.value, "color": "warning"},
        ]

        with self:
            for status_button in status_buttons:
                with Button(
                    classes="status-button",
                    click=on_status_clicked,
                    value=status_button["status"],
                    variant="tonal",
                    active_color=status_button["color"],
                ):
                    html.Div(status_button["status"])
                    html.Div(
                        f"{{{{ {status_state.name.counts}['{status_button['status']}'] }}}} EEG",
                        classes="text-caption",
                        v_if=f"'{status_button['status']}' in {status_state.name.counts}",
                    )
