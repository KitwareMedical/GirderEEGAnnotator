from trame_server.core import Server
from undo_stack import Signal

from girdereegannotator.database.exceptions import AuthenticationError
from girdereegannotator.utils.base_logic import BaseLogic

from .authentication_ui import AuthenticationState, AuthenticationUI


class AuthenticationLogic(BaseLogic[AuthenticationState]):
    user_connected = Signal()
    user_disconnected = Signal()

    def __init__(self, server: Server):
        super().__init__(server, AuthenticationState)
        self._current_user = self.get_sub_state(self.name.user_state)

    def set_current_user(self) -> None:
        if self._current_user.data._id is None:
            user = self.ctrl.get_me()
            if user is not None:
                self._current_user.set_dataclass(user)
                self.user_connected()

    def set_ui(self, ui: AuthenticationUI) -> None:
        ui.auth_dialog.login_clicked.connect(self._login)
        ui.auth_menu.logout_clicked.connect(self._logout)

    def _reset_state(self) -> None:
        self.typed_state.set_dataclass(AuthenticationState())

    def _login(self, username: str, password: str) -> None:
        try:
            user = self.ctrl.login(username, password)
            self._reset_state()
            self._current_user.set_dataclass(user)
            self.user_connected()

        except AuthenticationError as e:
            self.data.login_state.error = str(e)
            self.data.login_state.user_password = None

    def _logout(self) -> None:
        self._reset_state()
        self.user_disconnected()
        self.ctrl.logout()
