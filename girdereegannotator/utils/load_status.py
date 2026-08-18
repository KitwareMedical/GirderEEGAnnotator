from enum import Enum, auto

from trame.widgets.html import Div, Span
from trame.widgets.vuetify3 import VIcon, VProgressLinear


class LoadStatus(Enum):
    UNDEFINED = auto()
    LOADING = auto()
    LOADED = auto()
    ERROR = auto()


class LoadErrorMessage(Div):
    def __init__(self, status_message: str, **kwargs):
        super().__init__(classes="load-error-message", **kwargs)
        with self:
            VIcon(color="warning", icon="mdi-alert-circle", size=100)
            Span("{{ " + status_message + " }}")


class LoadProgress(VProgressLinear):
    def __init__(self, **kwargs):
        super().__init__(classes="load-progress", indeterminate=True, size=100, variant="split", rounded=True, **kwargs)
