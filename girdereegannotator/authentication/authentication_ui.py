from dataclasses import dataclass, field

from trame.widgets import html
from trame_server.utils.typed_state import TypedState

from girdereegannotator.database.models import User

from .components import LoginDialog, LoginState, UserProfileMenu


@dataclass
class AuthenticationState:
    user_state: User = field(default_factory=User)
    login_state: LoginState = field(default_factory=LoginState)
    is_menu_visible: bool = False


class AuthenticationUI(html.Div):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        auth_state = TypedState(self.state, AuthenticationState)
        user_state = auth_state.get_sub_state(auth_state.name.user_state)
        login_state = auth_state.get_sub_state(auth_state.name.login_state)

        with self:
            self.auth_menu = UserProfileMenu(
                v_if=user_state.name._id,
                v_model=auth_state.name.is_menu_visible,
                user_state=user_state,
            )
            self.auth_dialog = LoginDialog(v_else=True, login_state=login_state)
