from trame_server.core import Server

from girdereegannotator.utils.base_logic import BaseLogic

from ..authentication import AuthenticationLogic
from ..eeg_annotator import EGGAnnotatorLogic
from ..portal import PortalLogic
from .app_ui import AnnotatorAppState, AnnotatorAppUI


class AnnotatorAppLogic(BaseLogic[AnnotatorAppState]):
    def __init__(self, server: Server):
        super().__init__(server, AnnotatorAppState)

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
        self.data.is_drawer_open = is_connected

    def set_ui(self, ui: AnnotatorAppUI) -> None:
        self._eeg_annotator_logic.set_ui(ui.eeg_annotator_ui)
        self._auth_logic.set_ui(ui.auth_ui)
