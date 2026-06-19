from trame.ui.vuetify3 import VAppLayout
from trame.widgets import html, rca
from trame.widgets.vuetify3 import VMain
from trame_server import Server

from .eeg_annotator_shortcuts_panel import ShortcutsPanel


class EGGAnnotatorUI(html.Div):
    def __init__(self) -> None:
        super().__init__(classes="d-flex flex-column pb-2 fill-height")
        self._build_ui()

    def _build_ui(self) -> None:
        with self:
            self.rca = rca.RemoteControlledArea(ref="eegview", send_mouse_move=True)
            ShortcutsPanel()
