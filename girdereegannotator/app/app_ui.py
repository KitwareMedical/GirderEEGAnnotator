from dataclasses import dataclass

from trame.ui.vuetify3 import VAppLayout
from trame.widgets import client
from trame.widgets import vuetify3 as v3
from trame_server.core import Server
from trame_server.utils.typed_state import TypedState

from ..authentication import AuthenticationUI
from ..eeg_annotator import EGGAnnotatorUI
from ..portal import PortalUI


@dataclass
class AnnotatorAppState:
    app_name: str = "GirderEGGAnnotator"
    is_drawer_open: bool = False


class AnnotatorAppLayout(VAppLayout):
    def __init__(
        self,
        server: Server,
        **kwargs,
    ):
        super().__init__(server, **kwargs)
        self.typed_state = TypedState(self.state, AnnotatorAppState)
        self.state.trame__title = self.typed_state.data.app_name

        with self:
            with v3.VAppBar(border=True, flat=True, height=75) as self.app_bar:
                v3.VAppBarNavIcon(
                    icon="mdi-menu",
                    click=f"{self.typed_state.name.is_drawer_open} = !{self.typed_state.name.is_drawer_open}",
                )
                v3.VAppBarTitle(text=self.typed_state.data.app_name)

            self.app_drawer = v3.VNavigationDrawer(v_model=self.typed_state.name.is_drawer_open, width=350)

            self.app_annotator = v3.VMain(classes="main-app")


class AnnotatorAppUI:
    def __init__(self, server: Server):
        self.layout = AnnotatorAppLayout(server)

        with self.layout:
            client.Style(
                "html { overflow-y: hidden; } "
                ".main-app { height: 100vh; display: flex; flex-direction: column;}"
                ".display-area { padding-top: 2px; }"
                ".image-display-area { height: calc(100% - 2px); padding: 2px; border: 2px solid white;}"
                ".remote-controlled-area:focus .image-display-area { border: 2px dashed orange; }"
                ".v-input .v-input__prepend .v-icon { color: rgb(var(--v-theme-on-surface)); opacity: 1; }"
                ".v-main .v-application__wrap { min-height: 100%; }"
                ".v-main { max-height: 100%; }"
            )
            with self.layout.app_bar:
                self.auth_ui = AuthenticationUI()

            with self.layout.app_drawer:
                self.portal_ui = PortalUI()

            with self.layout.app_annotator:
                self.eeg_annotator_ui = EGGAnnotatorUI()
