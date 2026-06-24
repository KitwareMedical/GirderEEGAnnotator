from dataclasses import dataclass

from trame.widgets import html, rca
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState

from .eeg_annotator_shortcuts_panel import ShortcutsPanel


@dataclass
class EEGAnnotatorState:
    load_error: str | None = None


class EGGAnnotatorUI(html.Div):
    def __init__(self, loading: str, **kwargs) -> None:
        super().__init__(classes="fill-height", **kwargs)
        self.loading = loading
        self.typed_state = TypedState(self.state, EEGAnnotatorState)
        self._build_ui()

    def _build_ui(self) -> None:
        with self:
            with html.Div(
                v_if=(self.loading,),
                classes="d-flex flex-column justify-center align-center fill-height",
            ):
                v3.VProgressCircular(indeterminate=True, size=100)

            with html.Div(
                v_if=(self.typed_state.name.load_error,),
                classes="d-flex flex-column justify-center align-center fill-height",
            ):
                v3.VIcon(icon="mdi-alert-circle", size=100, color="warning")
                html.Span("{{ " + self.typed_state.name.load_error + " }}")

            with html.Div(classes="fill-height"):
                self.rca = rca.RemoteControlledArea(ref="eegview", send_mouse_move=True)
                ShortcutsPanel()
