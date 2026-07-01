from dataclasses import dataclass

from trame.app import TrameApp
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import client
from trame.widgets import vuetify3 as v3
from trame_server.core import Server
from trame_server.utils.typed_state import TypedState

from .authentication import AuthLogic, AuthUI
from .database.interface_database import (
    DatabaseInterface,
    register_interface,
)
from .eeg_annotator import EGGAnnotatorLogic, EGGAnnotatorUI
from .portal import PortalLogic, PortalUI


@dataclass
class AnnotatorState:
    app_name: str = "GirderEGGAnnotator"
    is_drawer_open: bool = False
    is_user_connected: bool = False
    is_eeg_loaded: bool = False


class AnnotatorLayout(VAppLayout):
    def __init__(
        self,
        server: Server,
        **kwargs,
    ):
        super().__init__(server, **kwargs)
        self.typed_state = TypedState(self.state, AnnotatorState)
        self.state.trame__title = self.typed_state.data.app_name

        with self:
            with v3.VAppBar(border=True, flat=True, height=75) as self.app_bar:
                v3.VAppBarNavIcon(
                    icon="mdi-menu",
                    click=f"{self.typed_state.name.is_drawer_open} = !{self.typed_state.name.is_drawer_open}",
                )
                v3.VAppBarTitle(text=self.typed_state.data.app_name)

            self.app_drawer = v3.VNavigationDrawer(v_model=self.typed_state.name.is_drawer_open, width=350)

            self.app_annotator = v3.VMain(v_if=(self.typed_state.name.is_user_connected), classes="main-app")

            with v3.VFooter(app=True, classes="my-0 py-0", border=True) as self.footer:
                v3.VProgressCircular(
                    indeterminate=("!!trame__busy",),
                    color="#04a94d",
                    size=16,
                    width=3,
                    classes="ml-n3 mr-1",
                )
                self.footer.add_child(
                    '<a href="https://kitware.github.io/trame/" '
                    'class="text-grey-lighten-1 text-caption text-decoration-none" '
                    'target="_blank">Powered by trame</a>'
                )
                v3.VSpacer()
                reload = self.server.controller.on_server_reload
                if reload.exists():
                    v3.VBtn(
                        size="x-small",
                        density="compact",
                        icon="mdi-autorenew",
                        elevation=0,
                        click=self.on_server_reload,
                        classes="mx-2",
                    )

                self.footer.add_child(
                    '<a href="https://www.kitware.com/" '
                    'class="text-grey-lighten-1 text-caption text-decoration-none" '
                    'target="_blank">© 2025 Kitware Inc.</a>'
                )


class AnnotatorUI:
    def __init__(self, server: Server):
        self.layout = AnnotatorLayout(server)
        self.portal_ui = PortalUI()
        self.auth_ui = AuthUI()
        self._build_ui()

    @property
    def typed_state(self) -> TypedState[AnnotatorState]:
        return self.layout.typed_state

    def _build_ui(self) -> None:
        with self.layout:
            client.Style(
                "html { overflow-y: hidden; } "
                ".main-app { height: 100vh; display: flex; flex-direction: column;}"
                ".image-display-area { height: calc(100% - 2px); width: calc(100% - 2px) !important; padding: 2px; border: 2px solid white;}"
                ".remote-controlled-area:focus .image-display-area { border: 2px dashed orange; }"
                ".v-input .v-input__prepend .v-icon { color: rgb(var(--v-theme-on-surface)); opacity: 1; }"
                ".v-main .v-application__wrap { min-height: 100%; }"
                ".v-main { max-height: 100%; }"
            )
            with self.layout.app_bar:
                self.portal_ui.build_bar(v_if=(self.typed_state.name.is_user_connected))
                v3.VSpacer()
                self.auth_ui.build_user_profile(v_if=(self.typed_state.name.is_user_connected))

            with self.layout.app_drawer:
                self.portal_ui.build_drawer()

            with self.layout.app_annotator:
                self.eeg_annotator_ui = EGGAnnotatorUI(v_if=(self.typed_state.name.is_eeg_loaded,))
                self.portal_ui.build_loader(v_else=True)

            self.auth_ui.build_dialog(v_if=(f"!{self.typed_state.name.is_user_connected}",))


class AnnotatorLogic:
    def __init__(self, server: Server):
        self.server = server
        self.typed_state = TypedState(server.state, AnnotatorState)

        self._eeg_annotator_logic = EGGAnnotatorLogic(self.server)

        self._portal_logic = PortalLogic(self.server)
        self._portal_logic.eeg_media_selected.connect(self._on_eeg_media_selected)
        self._portal_logic.loader_logic.eeg_media_downloaded.connect(self._on_eeg_media_downloaded)
        self._portal_logic.loader_logic.eeg_media_loaded.connect(self._on_eeg_media_loaded)

        self._auth_logic = AuthLogic(server)
        self._auth_logic.user_connected.connect(self._on_user_connected)

    def _on_user_connected(self, is_connected: bool) -> None:
        if is_connected:
            self._portal_logic.set_eeg_media_list()
        else:
            self._portal_logic.reset_state()
        self.typed_state.data.is_drawer_open = is_connected
        self.typed_state.data.is_user_connected = is_connected

    def _on_eeg_media_selected(self) -> None:
        self.typed_state.data.is_eeg_loaded = False

    def _on_eeg_media_downloaded(self, eeg_file_path: str) -> None:
        self._eeg_annotator_logic.set_file_path(eeg_file_path)

    def _on_eeg_media_loaded(self) -> None:
        self.typed_state.data.is_eeg_loaded = True

    def set_ui(self, ui: AnnotatorUI) -> None:
        self._eeg_annotator_logic.set_ui(ui.eeg_annotator_ui)
        self._portal_logic.set_ui(ui.portal_ui)
        self._auth_logic.set_ui(ui.auth_ui)


class AnnotatorApp(TrameApp):
    def __init__(self, server: Server, interface: DatabaseInterface):
        super().__init__(server)
        self.register_interface(interface)

        self._logic = AnnotatorLogic(self.server)
        self._ui = AnnotatorUI(self.server)

        self.set_ui()

    def set_ui(self) -> None:
        self._logic.set_ui(self._ui)

    def register_interface(self, interface: DatabaseInterface) -> None:
        """Link all database APIs to controller"""
        if interface is not None:
            register_interface(interface, self.ctrl)
