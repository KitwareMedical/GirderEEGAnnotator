from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from undo_stack import Signal

from girdereegannotator.utils.base_ui import BaseUI


@dataclass
class AlertsState:
    alerts: dict[int, dict[str, str | int | bool]] = field(default_factory=dict)


class AlertsUI(html.Div, BaseUI[AlertsState]):
    alert_removed = Signal(int)

    def __init__(self, **kwargs):
        super().__init__(classes="alerts-container", **kwargs)

        self._init_typed_state(self.state, AlertsState)
        with self, v3.VSlideYReverseTransition(group=True):
            v3.VAlert(
                v_for=f"(alert, alert_id) in {self.name.alerts}",
                key=("alert_id",),
                model_value=True,
                type=("alert.type",),
                title=("alert.title",),
                text=("alert.text",),
                density="compact",
                closable=True,
                click_close=(self.alert_removed, "[alert_id]"),
            )
