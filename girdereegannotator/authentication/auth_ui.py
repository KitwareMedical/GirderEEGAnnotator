from dataclasses import dataclass, field

from trame.widgets import vuetify3 as v3
from trame_server.core import Server
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import User


@dataclass
class AuthState:
    current_user: User = field(default_factory=User)
    user_login: str | None = None
    user_password: str | None = None


class AuthUI:
    login_clicked = Signal(str, str)
    logout_clicked = Signal(str, str)

    def __init__(self, server: Server, **kwargs) -> None:
        super().__init__(**kwargs)
        self.typed_state = TypedState(server.state, AuthState)

    def build_user_profile(self, **kwargs) -> None:
        v3.VBtn(
            "Logout",
            click=self.logout_clicked,
            color="error",
            **kwargs,
        )

    def build_dialog(self, **kwargs) -> None:
        with (
            v3.VDialog(
                model_value=True,
                persistent=True,
                width=500,
                **kwargs,
            ),
            v3.VForm(
                fast_fail=True,
                submit_prevent=(
                    self.login_clicked,
                    f"[{self.typed_state.name.user_login}, {self.typed_state.name.user_password}]",
                ),
                __events=[("submit_prevent", "submit.prevent")],
            ),
            v3.VCard(),
        ):
            with v3.VCardText(classes="pb-0"):
                v3.VTextField(
                    v_model=self.typed_state.name.user_login,
                    autocomplete="username",
                    autofocus=True,
                    placeholder="Login",
                )
                v3.VTextField(
                    v_model=self.typed_state.name.user_password,
                    autocomplete="current-password",
                    placeholder="Password",
                    type="password",
                )
            with v3.VCardActions():
                v3.VBtn("Submit", block=True, type="submit", __properties=["type"])
