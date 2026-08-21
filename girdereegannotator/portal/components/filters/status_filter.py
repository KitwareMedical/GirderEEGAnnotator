from dataclasses import dataclass, field
from enum import Enum

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.utils.components import Button


class Status(Enum):
    UNDEFINED = "All"
    TO_ANNOTATE = "To annotate"
    TO_VALIDATE = "To validate"
    VALIDATED = "Validated"


@dataclass
class StatusState:
    status: Status = Status.UNDEFINED
    counts: dict[Status, int] = field(default_factory=dict)


class StatusFilter(v3.VBtnToggle):
    def __init__(self, status_state: TypedState[StatusState], on_status_clicked: Signal, **kwargs):
        super().__init__(
            v_model=status_state.name.status,
            mandatory=True,
            **kwargs,
        )

        status_state.bind_changes({status_state.name.status: on_status_clicked})

        status_buttons = [
            {"status": Status.UNDEFINED.value, "color": "secondary"},
            {"status": Status.TO_ANNOTATE.value, "color": "warning"},
            {"status": Status.TO_VALIDATE.value, "color": "info"},
            {"status": Status.VALIDATED.value, "color": "success"},
        ]

        with self:
            for status_button in status_buttons:
                with Button(
                    classes="mx-1 status-button",
                    value=status_button["status"],
                    active_color=status_button["color"],
                    width=130,
                ):
                    html.Div(status_button["status"])
                    html.Div(
                        f"{{{{ {status_state.name.counts}['{status_button['status']}'] }}}} EEG",
                        classes="text-caption",
                        v_if=f"'{status_button['status']}' in {status_state.name.counts}",
                    )
                    v3.VProgressCircular(
                        v_else=True,
                        indeterminate=True,
                        size=15,
                        width=3,
                    )
