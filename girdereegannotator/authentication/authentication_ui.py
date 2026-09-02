from dataclasses import dataclass, field

from trame.widgets import html
from trame_server.utils.typed_state import TypedState

from girdereegannotator.database.models import User
from girdereegannotator.utils.base_ui import BaseUI
from girdereegannotator.utils.components import Button

from .components import LoginDialog, LoginState, UserProfileMenu


@dataclass
class AuthenticationState:
    login_state: LoginState = field(default_factory=LoginState)
    is_menu_visible: bool = False


class AuthenticationUI(html.Div, BaseUI[AuthenticationState]):
    def __init__(self, **kwargs) -> None:
        super().__init__(classes="pa-1 d-flex justify-center", **kwargs)
        self._init_typed_state(self.state, AuthenticationState)
        user_state = TypedState(self.state, User)

        with self:
            self.auth_menu = UserProfileMenu(
                v_if=user_state.name._id,
                v_model=self.name.is_menu_visible,
            )
            Button(v_else=True, icon="mdi-account", color="secondary")

        self.auth_dialog = LoginDialog(
            v_if=f"!{user_state.name._id}", login_state=self.get_sub_state(self.name.login_state)
        )
