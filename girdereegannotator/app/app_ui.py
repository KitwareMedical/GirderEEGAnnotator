from dataclasses import dataclass, field

from trame.ui.vuetify3 import VAppLayout
from trame.widgets import client, html
from trame.widgets import vuetify3 as v3
from trame_server.core import Server

from girdereegannotator.utils.base_ui import BaseUI

from ..authentication import AuthenticationUI
from ..eeg_annotator import EGGAnnotatorUI
from ..portal import PortalUI
from .components.navigation_card import NavigationCard, NavigationState


@dataclass
class AnnotatorAppState:
    app_name: str = "GirderEGGAnnotator"
    nav_state: NavigationState = field(default_factory=NavigationState)


class AnnotatorAppLayout(VAppLayout, BaseUI[AnnotatorAppState]):
    def __init__(
        self,
        server: Server,
        **kwargs,
    ):
        super().__init__(server, **kwargs)
        self._init_typed_state(self.state, AnnotatorAppState)
        self.state.trame__title = self.data.app_name

        with self:
            with html.Div(classes="app-bar") as self.app_bar:
                v3.VIcon(icon="mdi-heart-pulse", size="x-large", color="primary", classes="mx-4")
                v3.VAppBarTitle(text=(self.name.app_name,))
                v3.VSpacer()
            with v3.VMain(classes="app-main"):
                self.app_navigation = NavigationCard(self.get_sub_state(self.name.nav_state))


class AnnotatorAppUI:
    def __init__(self, server: Server):
        self.layout = AnnotatorAppLayout(server)

        with self.layout:
            client.Style(
                "html { overflow-y: hidden; } "
                ".annotator-window { border: 2px dashed transparent; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; }"
                ".annotator-window:focus-within { border-color: orange; }"
                ".nav-window { height: 100%; }"
                ".app-bar { height: 60px; display: flex; align-items: center;}"
                ".app-main { height: calc(100vh - 60px); padding-left: 8px; padding-right: 8px; padding-bottom: 8px }"
                ".browser { height: 100vh; display: flex; flex-direction: column; overflow-y: auto}"
                ".annotator { height: 100vh; display: flex; flex-direction: column;}"
                ".image-display-area { height: calc(100% - 2px); padding: 2px; }"
                ".nav-bar { display: flex; justify-content: space-between; height: 65px; }"
                ".nav-content { height: calc(100% - 65px); padding: 0px; }"
                ".portal { padding-left: 20px; padding-right: 20px; display: flex; flex-direction: column; height: 100%}"
                ".portal-list { height: calc(100% - 50px); padding: 0px; }"
                ".portal-list-item { margin-top: 4px;}"
                ".portal-pagination { height: 50px; display: flex; width: 100%; align-items: center; justify-content: center; }"
                ".remote-controlled-area:focus-visible { outline: none !important; }"
                ".v-btn--variant-plain { opacity: 1; } "
                ".v-input .v-input__prepend .v-icon { color: rgb(var(--v-theme-on-surface)); opacity: 1; }"
                ".v-main .v-application__wrap { min-height: 100%; }"
                ".v-main { max-height: 100%; }"
            )
            with self.bar:
                self.auth_ui = AuthenticationUI()

            with self.navigation.portal:
                self.portal_ui = PortalUI()

            with self.navigation.portal_breadcrumbs:
                self.portal_ui.build_breadcrumbs()

            with self.navigation.annotator:
                self.eeg_annotator_ui = EGGAnnotatorUI()

    @property
    def bar(self) -> html.Div:
        return self.layout.app_bar

    @property
    def navigation(self) -> html.Div:
        return self.layout.app_navigation
