from trame_server.core import Controller, Server
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.exceptions import AuthenticationError

from .authentication_ui import AuthenticationState, AuthenticationUI


class AuthenticationLogic:
    user_connected = Signal(bool)

    def __init__(self, server: Server):
        self.server = server
        self.typed_state = TypedState(self.server.state, AuthenticationState)
        self._current_user = self.typed_state.get_sub_state(self.name.user_state)

        self.server.controller.on_client_connected.add(self._set_current_user)

    @property
    def name(self) -> AuthenticationState:
        return self.typed_state.name

    @property
    def data(self) -> AuthenticationState:
        return self.typed_state.data

    @property
    def ctrl(self) -> Controller:
        return self.server.controller

    def _set_current_user(self, **_kwargs) -> None:
        if self._current_user.data._id is None:
            user = self.ctrl.get_me()
            if user is not None:
                self._current_user.set_dataclass(user)
                self.user_connected(True)
            self.server.state.flush()

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
            self.user_connected(True)

        except AuthenticationError as e:
            self.data.login_state.error = str(e)
            self.data.login_state.user_password = None

    def _logout(self) -> None:
        self._reset_state()
        self.user_connected(False)
        self.ctrl.logout()
