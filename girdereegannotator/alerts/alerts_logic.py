import asyncio

from trame_server.core import Server

from girdereegannotator.utils.base_logic import BaseLogic

from .alerts_ui import Alert, AlertsState, AlertType


class AlertsLogic(BaseLogic[AlertsState]):
    _next_alert_id = 0

    def __init__(self, server: Server) -> None:
        super().__init__(server, AlertsState)

        self.ctrl.create_alert.add(self._create_alert)
        self.ctrl.create_warning_alert.add(self._create_warning_alert)
        self.ctrl.create_success_alert.add(self._create_success_alert)
        self.ctrl.create_error_alert.add(self._create_error_alert)

    def _create_alert(
        self, alert_text: str, alert_title: str | None = None, alert_level: AlertType = AlertType.INFO
    ) -> None:
        new_alert = Alert(id=self._next_alert_id, title=alert_title, text=alert_text, type=alert_level.value)
        self._next_alert_id += 1

        alerts = dict(self.data.alerts)
        alerts.update({new_alert.id: new_alert})
        self.data.alerts = alerts

        if alert_level.value < AlertType.WARNING.value:
            self.create_async_task(self._defer_remove_alert, new_alert.id)

    def _create_warning_alert(self, alert_text: str, alert_title: str | None = None) -> None:
        self._create_alert(alert_text, alert_title, AlertType.WARNING)

    def _create_success_alert(self, alert_text: str, alert_title: str | None = None) -> None:
        self._create_alert(alert_text, alert_title, AlertType.SUCCESS)

    def _create_error_alert(self, alert_text: str, alert_title: str | None = None) -> None:
        self._create_alert(alert_text, alert_title, AlertType.ERROR)

    def _remove_alert(self, alert_id: int) -> None:
        alerts = dict(self.data.alerts)

        if alert_id in alerts:
            del alerts[alert_id]
            self.data.alerts = alerts

    async def _defer_remove_alert(self, alert_id: int) -> None:
        """Asynchronously defer the deletion of alert"""
        await asyncio.sleep(5)
        self._remove_alert(alert_id)
