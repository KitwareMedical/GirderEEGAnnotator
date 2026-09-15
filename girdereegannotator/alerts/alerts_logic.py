from trame_alerts.core.service import AlertsService, AlertType
from trame_server.core import Server

from girdereegannotator.utils.base_logic import BaseLogic

from .alerts_ui import AlertsState, AlertsUI


class AlertsLogic(BaseLogic[AlertsState]):
    def __init__(self, server: Server) -> None:
        super().__init__(server, AlertsState)

        self._alerts_service = AlertsService(server, alerts_key=self.name.alerts)

        self.ctrl.create_alert.add(self._create_alert)
        self.ctrl.create_warning_alert.add(
            lambda text, **kwargs: self._create_alert(text, alert_type="warning", **kwargs)
        )
        self.ctrl.create_success_alert.add(
            lambda text, **kwargs: self._create_alert(text, alert_type="success", **kwargs)
        )
        self.ctrl.create_error_alert.add(lambda text, **kwargs: self._create_alert(text, alert_type="error", **kwargs))

    def _create_alert(self, text: str, alert_type: AlertType = "info", **kwargs) -> None:
        match alert_type:
            case "info":
                self._alerts_service.create_info_alert(text=text, **kwargs)
            case "success":
                self._alerts_service.create_success_alert(text=text, **kwargs)
            case "error":
                kwargs.setdefault("persistent", True)
                self._alerts_service.create_error_alert(text=text, **kwargs)
            case "warning":
                kwargs.setdefault("persistent", True)
                self._alerts_service.create_warning_alert(text=text, **kwargs)

    def set_ui(self, ui: AlertsUI) -> None:
        ui.alert_removed.connect(self._alerts_service.remove_alert)
