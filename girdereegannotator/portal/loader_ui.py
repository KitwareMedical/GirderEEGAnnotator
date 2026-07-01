from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState

from girdereegannotator.database.models import EEGMediaFile


@dataclass
class LoaderState:
    eeg_loading: bool = False
    eeg_file: EEGMediaFile = field(default_factory=EEGMediaFile)
    eeg_annotation_file: EEGMediaFile = field(default_factory=EEGMediaFile)
    load_error: str | None = None


class LoaderUI(html.Div):
    def __init__(self, **kwargs) -> None:
        super().__init__(classes="d-flex flex-column justify-center align-center fill-height", **kwargs)
        self.typed_state = TypedState(self.state, LoaderState)
        self._build_ui()

    def _build_ui(self) -> None:
        with self:
            v3.VProgressCircular(v_if=(self.typed_state.name.eeg_loading,), indeterminate=True, size=100)
            with html.Div(
                v_if=(f"!{self.typed_state.name.eeg_loading} && {self.typed_state.name.load_error}",),
            ):
                v3.VIcon(color="warning", icon="mdi-alert-circle", size=100)
                html.Span("{{ " + self.typed_state.name.load_error + " }}")
