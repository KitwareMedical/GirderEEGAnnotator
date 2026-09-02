from trame_server.core import Server
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.exceptions import AuthenticationError
from girdereegannotator.database.models import User
from girdereegannotator.utils.base_logic import BaseLogic

from .authentication_ui import AuthenticationState, AuthenticationUI


class AuthenticationLogic(BaseLogic[AuthenticationState]):
    user_updated = Signal(str | None)

    def __init__(self, server: Server):
        super().__init__(server, AuthenticationState)
        self._current_user = TypedState(self.state, User)

        self._current_user.bind_changes({self._current_user.name._id: self.user_updated})

    def update_current_user(self) -> None:
        if self._current_user.data._id is None:
            user = self.ctrl.get_me()
            if user is not None:
                self._current_user.set_dataclass(user)

    def set_ui(self, ui: AuthenticationUI) -> None:
        ui.auth_dialog.login_clicked.connect(self._login)
        ui.auth_menu.logout_clicked.connect(self._logout)

    def reset_state(self) -> None:
        super().reset_state()
        self._current_user.set_dataclass(User())

    def _login(self, username: str, password: str) -> None:
        try:
            user = self.ctrl.login(username, password)
            super().reset_state()
            self._current_user.set_dataclass(user)

        except AuthenticationError as e:
            self.data.login_state.error = str(e)
            self.data.login_state.user_password = None

    def _logout(self) -> None:
        self.reset_state()
        self.ctrl.logout()
