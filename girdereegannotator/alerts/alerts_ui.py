from dataclasses import dataclass, field
from enum import Enum

from trame.widgets import html
from trame.widgets import vuetify3 as v3

from girdereegannotator.utils.base_ui import BaseUI


class AlertType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Alert:
    id: int = 0
    title: str | None = None
    text: str | None = None
    type: AlertType = AlertType.INFO


@dataclass
class AlertsState:
    alerts: dict[int, Alert] = field(default_factory=list)


class AlertsUI(html.Div, BaseUI[AlertsState]):
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
            )
