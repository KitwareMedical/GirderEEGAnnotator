from dataclasses import dataclass, field
from enum import Enum

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState

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
    def __init__(self, status_state: TypedState[StatusState], **kwargs):
        super().__init__(
            v_model=status_state.name.status,
            mandatory=True,
            **kwargs,
        )

        status_buttons = [
            {"status": Status.UNDEFINED.value, "color": "undefined", "tooltip": None},
            {"status": Status.TO_DO.value, "color": "secondary", "tooltip": "Show EEGs with 0 annotations"},
            {
                "status": Status.IN_PROGRESS.value,
                "color": "warning",
                "tooltip": "Show EEGs with at least 1 annotations in progress",
            },
            {
                "status": Status.IN_REVIEW.value,
                "color": "info",
                "tooltip": "Show EEGs with at least 1 annotations in review",
            },
            {"status": Status.DONE.value, "color": "success", "tooltip": "Show annotated and approved EEGs"},
        ]

        with self:
            for status_button in status_buttons:
                with Button(
                    classes="mx-1 status-button",
                    value=status_button["status"],
                    color=status_button["color"],
                    width=130,
                    tooltip=status_button["tooltip"],
                    tooltip_open_delay=800,
                    tooltip_location="top",
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
