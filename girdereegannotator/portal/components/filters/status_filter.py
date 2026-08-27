from dataclasses import dataclass, field
from enum import Enum

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.utils.components import Button


class Status(Enum):
    UNDEFINED = "All"
    TO_DO = "To do"
    IN_PROGRESS = "In progress"
    IN_REVIEW = "In review"
    DONE = "Done"


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
            {"status": Status.UNDEFINED.value, "color": "undefined"},
            {"status": Status.TO_DO.value, "color": "secondary"},
            {"status": Status.IN_PROGRESS.value, "color": "warning"},
            {"status": Status.IN_REVIEW.value, "color": "info"},
            {"status": Status.DONE.value, "color": "success"},
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
                    with v3.VFadeTransition(mode="out-in"):
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
