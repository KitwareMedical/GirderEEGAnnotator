from dataclasses import dataclass

from trame.app import TrameApp
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import client
from trame.widgets import vuetify3 as v3
from trame_server.core import Server
from trame_server.utils.typed_state import TypedState

from girdereegannotator.database.interface_database import DatabaseInterface, register_interface
from girdereegannotator.portal.portal_logic import PortalLogic

from .eeg_annotator import EGGAnnotatorLogic, EGGAnnotatorUI
from .portal import PortalLogic, PortalUI

@dataclass
class AnnotatorState:
    app_name: str = "GirderEGGAnnotator"
    is_drawer_open: bool = True


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
            with v3.VAppBar(height=75) as self.app_bar:
                v3.VAppBarNavIcon(
                    icon="mdi-menu",
                    click=f"{self.typed_state.name.is_drawer_open} = !{self.typed_state.name.is_drawer_open}"
                )

            self.app_drawer = v3.VNavigationDrawer(v_model=self.typed_state.name.is_drawer_open)

            self.app_annotator = v3.VMain(classes="main-app d-flex flex-column")

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
        self.portal_ui = PortalUI(server)
        self._build_ui()
    
    def _build_ui(self) -> None:
        with self.layout:
            client.Style(
                "html { overflow-y: hidden; } "
                ".main-app { height: 100vh; }"
                ".main-view { display: flex; flex-direction: column; height: 100%; }"
                ".v-input .v-input__prepend .v-icon { color: rgb(var(--v-theme-on-surface)); opacity: 1; }"
                ".v-main .v-application__wrap { min-height: 100%; }"
                ".v-main { max-height: 100%; }"
            )
            with self.layout.app_bar:
                self.portal_ui.build_bar()

            with self.layout.app_drawer:
                self.portal_ui.build_drawer()

            with self.layout.app_annotator:
                self.eeg_annotator_ui = EGGAnnotatorUI()


class AnnotatorLogic:
    def __init__(self, server: Server):
        self.server = server
        self._eeg_annotator_logic = EGGAnnotatorLogic(self.server)
        
        self._portal_logic = PortalLogic(self.server)
        self._portal_logic.eeg_media_loaded.connect(self._on_eeg_files_loaded)

    def _on_eeg_files_loaded(self, eeg_file_path: str) -> None:
        self._eeg_annotator_logic.set_file_path(eeg_file_path)

    def set_ui(self, ui: AnnotatorUI) -> None:
        self._eeg_annotator_logic.set_ui(ui.eeg_annotator_ui)
        self._portal_logic.set_ui(ui.portal_ui)


class AnnotatorApp(TrameApp):
    def __init__(self, server: Server, interface: DatabaseInterface):
        super().__init__(server)
        self.register_interface(interface)

        self._logic = AnnotatorLogic(self.server)
        self._ui = AnnotatorUI(self.server)

        self.set_ui()

    def set_ui(self) -> None:
        self._logic.set_ui(self._ui)

    def register_interface(self, interface) -> None:
        """Link all database APIs to controller"""
        if interface is not None:
            register_interface(interface, self.ctrl)