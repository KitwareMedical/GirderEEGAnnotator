from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3

from girdereegannotator.database.models import User
from girdereegannotator.utils.base_ui import BaseUI

from .components import LoginDialog, LoginState, UserProfileMenu


@dataclass
class AuthenticationState:
    user_state: User = field(default_factory=User)
    login_state: LoginState = field(default_factory=LoginState)
    is_menu_visible: bool = False


class AuthenticationUI(html.Div, BaseUI[AuthenticationState]):
    def __init__(self, **kwargs) -> None:
        super().__init__(classes="pa-1 d-flex justify-center", **kwargs)
        self._init_typed_state(self.state, AuthenticationState)

        with self:
            self.auth_menu = UserProfileMenu(
                v_if=self.name.user_state._id,
                v_model=self.name.is_menu_visible,
                user_state=self.get_sub_state(self.name.user_state),
            )
            v3.VBtn(v_else=True, icon="mdi-account", variant="text")

        self.auth_dialog = LoginDialog(
            v_if=f"!{self.name.user_state._id}", login_state=self.get_sub_state(self.name.login_state)
        )
