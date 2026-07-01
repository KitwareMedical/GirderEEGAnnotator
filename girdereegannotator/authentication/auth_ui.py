from collections.abc import Callable
from dataclasses import dataclass, field

from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import User


@dataclass
class AuthState:
    current_user: User = field(default_factory=User)
    user_login: str | None = None
    user_password: str | None = None
    error: str | None = None
    loading: bool = False


class AuthTextField(v3.VTextField):
    def __init__(self, label: str, **kwargs) -> None:
        kwargs["label"] = label
        kwargs["variant"] = "solo-filled"
        kwargs["flat"] = True
        super().__init__(rules=(f"[ value => !!value ||  '{label} required' ]",), **kwargs)


class AuthDialog(v3.VDialog):
    def __init__(self, login_callable: Callable, **kwargs) -> None:
        super().__init__(model_value=True, persistent=True, width=500, **kwargs)
        self.typed_state = TypedState(self.state, AuthState)

        with (
            self,
            v3.VForm(
                v_slot="{ isValid }",
                fast_fail=True,
                submit_prevent=(
                    f"{self.typed_state.name.loading} = true; "
                    f"trigger('{self.ctrl.trigger_name(login_callable)}', "
                    f"[{self.typed_state.name.user_login}, {self.typed_state.name.user_password}])"
                    ".finally(() => {"
                    f"{self.typed_state.name.loading} = false;"
                    "})"
                ),
                __events=[("submit_prevent", "submit.prevent")],
            ),
            v3.VCard(),
        ):
            with v3.VCardText(classes="pb-0"):
                v3.VAlert(
                    v_if=(f"{self.typed_state.name.error} && !{self.typed_state.name.loading}",),
                    closable=True,
                    text=(self.typed_state.name.error,),
                    type="error",
                    variant="tonal",
                )
                AuthTextField(
                    v_model=self.typed_state.name.user_login,
                    autocomplete="username",
                    autofocus=True,
                    label="Login",
                    prepend_inner_icon="mdi-account",
                )
                AuthTextField(
                    v_model=self.typed_state.name.user_password,
                    autocomplete="current-password",
                    label="Password",
                    type="password",
                    prepend_inner_icon="mdi-lock",
                )
            with v3.VCardActions():
                v3.VBtn(
                    "Log In",
                    block=True,
                    disabled=("!isValid.value",),
                    loading=(self.typed_state.name.loading,),
                    type="submit",
                    variant="tonal",
                    __properties=["type"],
                )


class AuthProfile(v3.VBtn):
    def __init__(self, logout_callable: Callable, **kwargs):
        super().__init__("Logout", click=logout_callable, color="error", **kwargs)


class AuthUI:
    login_clicked = Signal(str, str)
    logout_clicked = Signal(str, str)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def build_user_profile(self, **kwargs) -> None:
        AuthProfile(self.logout_clicked, **kwargs)

    def build_dialog(self, **kwargs) -> None:
        AuthDialog(self.login_clicked, **kwargs)
