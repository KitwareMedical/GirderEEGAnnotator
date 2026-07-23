from dataclasses import dataclass

from trame.app import TrameApp
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import client
from trame.widgets import vuetify3 as v3
from trame_server.core import Server
from trame_server.utils.typed_state import TypedState

from .authentication import AuthenticationLogic, AuthenticationUI
from .database.interface_database import (
    DatabaseInterface,
    register_interface,
)
from .eeg_annotator import EGGAnnotatorLogic, EGGAnnotatorUI
from .portal import PortalLogic, PortalUI


@dataclass
class AnnotatorAppState:
    app_name: str = "GirderEGGAnnotator"
    is_drawer_open: bool = False
    is_viewer_disabled: bool = False


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

    @property
    def typed_state(self) -> TypedState[AnnotatorAppState]:
        return self.layout.typed_state


class AnnotatorAppLogic:
    def __init__(self, server: Server):
        self.server = server
        self.typed_state = TypedState(server.state, AnnotatorAppState)

        self._eeg_annotator_logic = EGGAnnotatorLogic(self.server)
        self._portal_logic = PortalLogic(self.server)
        self._auth_logic = AuthenticationLogic(server)

        self._eeg_annotator_logic.next_clicked.connect(self._portal_logic.select_next_eeg)
        self._eeg_annotator_logic.previous_clicked.connect(self._portal_logic.select_previous_eeg)
        self._eeg_annotator_logic.eeg_media_updated.connect(self._portal_logic.update_eeg_media_list)

        self._portal_logic.eeg_media_selected.connect(self._eeg_annotator_logic.load_eeg_media)

        self._auth_logic.user_connected.connect(self._on_user_connected)

    def _on_user_connected(self, is_connected: bool) -> None:
        self._portal_logic.reset_state()
        self._eeg_annotator_logic.reset_state()
        self.typed_state.data.is_drawer_open = is_connected

    def set_ui(self, ui: AnnotatorAppUI) -> None:
        self._eeg_annotator_logic.set_ui(ui.eeg_annotator_ui)
        self._auth_logic.set_ui(ui.auth_ui)


class AnnotatorApp(TrameApp):
    def __init__(self, server: Server, interface: DatabaseInterface):
        super().__init__(server)
        self.register_interface(interface)

        self._logic = AnnotatorAppLogic(self.server)
        self._ui = AnnotatorAppUI(self.server)

        self.set_ui()

    def set_ui(self) -> None:
        self._logic.set_ui(self._ui)

    def register_interface(self, interface: DatabaseInterface) -> None:
        """Link all database APIs to controller"""
        if interface is not None:
            register_interface(interface, self.ctrl)
