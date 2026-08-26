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
            box_shadow = (
                "0 2px 1px -1px var(--v-shadow-key-umbra-opacity, #0003), "
                "0 1px 1px -1px var(--v-shadow-key-penumbra-opacity, #00000024), "
                "0 1px 3px -1px var(--v-shadow-key-ambient-opacity, #0000001f)"
            )

            client.Style(
                "html { overflow-y: hidden; } "
                ".annotator { height: 100vh; display: flex; flex-direction: column;}"
                ".annotator-window { border: 2px dashed transparent; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; }"
                ".annotator-window:focus-within { border-color: orange; }"
                ".annotation-list-item .v-list-item__content { display: flex; align-items: center; gap: 8px; }"
                ".annotation-list-item:hover { background-color: color-mix(in srgb, rgb(var(--v-theme-surface)) 95%, rgb(var(--v-theme-primary))); }"
                ".app-bar { height: 60px; display: flex; align-items: center; color: rgb(var(--v-theme-secondary)); }"
                ".app-main { height: calc(100vh - 60px); padding-left: 8px; padding-right: 8px; padding-bottom: 8px }"
                ".breadcrumbs-button { opacity: 1 !important; padding: 0px; } "
                ".button-bar { display: flex; align-items: center; gap: 8px;}"
                ".list-filters { height: 60px; display: flex; align-items: center; gap: 8px; justify-content: end; }"
                ".list-filters .v-input__control { width: 200px; }"
                ".list-filters .v-label { color: rgb(var(--v-theme-secondary)); }"
                ".expandable-list { height: calc(100% - 60px); }"
                ".expandable-list__load { height: 5px; }"
                ".expandable-list__error { height: calc(100% - 5px); }"
                ".expandable-list__content { height: calc(100% - 5px); }"
                ".expandable-list__content-list { height: calc(100% - 30px); padding: 0px; }"
                ".expandable-list__content-count { display: flex; justify-content: end; align-items: center; height: 30px; color: rgb(var(--v-theme-secondary)); }"
                f".expandable-list-item {{ background-color: rgb(var(--v-theme-surface-variant)); margin-top: 4px; box-shadow: {box_shadow}; height: 50px; }}"
                ".expandable-list-item--expanded { border-bottom-left-radius: 0px; border-bottom-right-radius: 0px; box-shadow: none; }"
                f".expansion-card {{ border-top-left-radius: 0px; border-top-right-radius: 0px; box-shadow: {box_shadow}; padding: 12px; }}"
                ".image-display-area { height: calc(100% - 2px); padding: 2px; }"
                ".load-error-message { display: flex; justify-content: center; align-items: center; height: 100%; }"
                ".load-progress .v-progress-linear__indeterminate { animation-duration: 1s; }"
                ".metadata-content { display: flex; justify-content: space-between; align-items: center; gap:8px; }"
                ".metadata-ellipsis { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }"
                ".metadata-item { width: 50%; }"
                ".metadata-list { display: flex; flex-wrap: wrap; }"
                ".nav-bar { height: 65px; }"
                ".nav-bar .v-card-item__content { display: flex; align-items: center; justify-content: space-between; }"
                ".nav-content { height: calc(100% - 65px); padding: 0px; }"
                ".nav-window { height: 100%; }"
                ".portal { padding-left: 20px; padding-right: 20px; padding-bottom: 10px; height: 100%;}"
                ".remote-controlled-area:focus-visible { outline: none !important; }"
                ".search-input { display: flex; align-items: center; border-radius: 24px; background-color: rgb(var(--v-theme-surface-variant)); }"
                ".search-input .v-field { background-color: inherit; }"
                ".status-button .v-btn__content { display: flex; flex-direction: column; gap: 4px;}"
                ".status-button { background-color: rgb(var(--v-theme-surface-variant)); color: rgb(var(--v-theme-on-surface-variant))}"
                ".v-input .v-input__prepend .v-icon { color: rgb(var(--v-theme-on-surface)); opacity: 1; }"
                ".v-input__details:has(.v-messages:empty) { display: none; }"
                ".v-main .v-application__wrap { min-height: 100%; }"
                ".v-main { max-height: 100%; }"
            )
            with self.bar:
                self.auth_ui = AuthenticationUI()

            with self.navigation.portal:
                self.portal_ui = PortalUI()

            with self.navigation.portal_breadcrumbs:
                self.portal_ui.build_breadcrumbs()

            with self.navigation.portal_toolbar:
                self.portal_ui.build_toolbar()

            with self.navigation.annotator:
                self.eeg_annotator_ui = EGGAnnotatorUI()

    @property
    def bar(self) -> html.Div:
        return self.layout.app_bar

    @property
    def navigation(self) -> html.Div:
        return self.layout.app_navigation
