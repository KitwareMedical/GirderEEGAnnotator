from trame_server.core import Server

from girdereegannotator.database.models import EEGFileset, User
from girdereegannotator.utils.base_logic import BaseLogic

from ..authentication import AuthenticationLogic
from ..eeg_annotator import EGGAnnotatorLogic
from ..portal import PortalLogic
from .app_ui import AnnotatorAppState, AnnotatorAppUI
from .components.navigation_card import NavigationWindow


class AnnotatorAppLogic(BaseLogic[AnnotatorAppState]):
    def __init__(self, server: Server):
        super().__init__(server, AnnotatorAppState)

        self._portal_logic = PortalLogic(self.server)
        self._eeg_annotator_logic = EGGAnnotatorLogic(self.server)
        self._auth_logic = AuthenticationLogic(server)

        self._eeg_annotator_logic.next_clicked.connect(self._portal_logic.select_next_eeg)
        self._eeg_annotator_logic.previous_clicked.connect(self._portal_logic.select_previous_eeg)
        self._eeg_annotator_logic.eeg_fileset_updated.connect(self._portal_logic.update_eeg_fileset_list)

        self._portal_logic.eeg_fileset_unselected.connect(self._on_eeg_fileset_unselected)
        self._portal_logic.eeg_fileset_selected.connect(self._on_eeg_fileset_selected)

        self._auth_logic.user_updated.connect(self._on_user_updated)

        self.ctrl.on_client_connected.add(self._on_client_connected)

    def _on_client_connected(self, **_kwargs) -> None:
        if self.data.nav_state.window == NavigationWindow.UNDEFINED:
            self._auth_logic.update_current_user()

        elif self.data.nav_state.window == NavigationWindow.PORTAL:
            self._portal_logic.refresh()
        self.state.flush()

    def _on_user_updated(self, user: User) -> None:
        if user._id is not None:
            self._portal_logic.refresh()
            self.data.nav_state.window = NavigationWindow.PORTAL
            return

        self._portal_logic.reset_state()
        self._eeg_annotator_logic.reset_state()
        self.data.nav_state.window = NavigationWindow.UNDEFINED

    def _on_eeg_fileset_selected(self, eeg_fileset: EEGFileset) -> None:
        self._eeg_annotator_logic.load_eeg_fileset(eeg_fileset)
        self.data.nav_state.window = NavigationWindow.ANNOTATOR

    def _on_eeg_fileset_unselected(self) -> None:
        self.data.nav_state.window = NavigationWindow.PORTAL

    def set_ui(self, ui: AnnotatorAppUI) -> None:
        self._eeg_annotator_logic.set_ui(ui.eeg_annotator_ui)
        self._auth_logic.set_ui(ui.auth_ui)
        self._portal_logic.set_ui(ui.portal_ui)
