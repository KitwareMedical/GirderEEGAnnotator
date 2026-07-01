from trame_server.core import Controller, Server
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.exceptions import AuthenticationError

from .auth_ui import AuthState, AuthUI


class AuthLogic:
    user_connected = Signal(bool)

    def __init__(self, server: Server):
        self.server = server
        self.typed_state = TypedState(self.server.state, AuthState)
        self._current_user = self.typed_state.get_sub_state(self.name.current_user)

        self.server.controller.on_server_ready.add(self._set_current_user)

    @property
    def name(self) -> AuthState:
        return self.typed_state.name

    @property
    def data(self) -> AuthState:
        return self.typed_state.data

    @property
    def ctrl(self) -> Controller:
        return self.server.controller

    def _set_current_user(self, **_kwargs) -> None:
        user = self.ctrl.get_me()
        if user is not None:
            self._current_user.set_dataclass(user)
            self.user_connected(True)

    def set_ui(self, ui: AuthUI) -> None:
        ui.login_clicked.connect(self._login)
        ui.logout_clicked.connect(self._logout)

    def _reset_state(self) -> None:
        self.typed_state.set_dataclass(AuthState())

    def _login(self, username: str, password: str) -> None:
        try:
            user = self.ctrl.login(username, password)
            self._reset_state()
            self._current_user.set_dataclass(user)
            self.user_connected(True)

        except AuthenticationError as e:
            self.data.error = str(e)
            self.data.user_password = None

    def _logout(self) -> None:
        self._reset_state()
        self.user_connected(False)
        self.ctrl.logout()
