from dataclasses import dataclass

from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.utils.components import Button


@dataclass
class LoginState:
    user_login: str | None = None
    user_password: str | None = None
    error: str | None = None
    loading: bool = False


class LoginTextField(v3.VTextField):
    def __init__(self, label: str, **kwargs) -> None:
        kwargs["label"] = label
        kwargs["variant"] = "solo-filled"
        kwargs["flat"] = True
        super().__init__(rules=(f"[ value => !!value ||  '{label} required' ]",), **kwargs)


class LoginDialog(v3.VDialog):
    login_clicked = Signal(str, str)

    def __init__(self, login_state: TypedState[LoginState], **kwargs) -> None:
        super().__init__(model_value=True, persistent=True, width=500, **kwargs)

        with (
            self,
            v3.VForm(
                v_slot="{ isValid }",
                fast_fail=True,
                submit_prevent=(
                    f"{login_state.name.loading} = true; "
                    f"trigger('{self.ctrl.trigger_name(self.login_clicked)}', "
                    f"[{login_state.name.user_login}, {login_state.name.user_password}])"
                    ".finally(() => {"
                    f"{login_state.name.loading} = false;"
                    "})"
                ),
                __events=[("submit_prevent", "submit.prevent")],
            ),
            v3.VCard(),
        ):
            with v3.VCardText(classes="pb-0"):
                v3.VAlert(
                    v_if=f"{login_state.name.error} && !{login_state.name.loading}",
                    closable=True,
                    text=(login_state.name.error,),
                    type="error",
                    variant="tonal",
                )
                LoginTextField(
                    v_model=login_state.name.user_login,
                    autocomplete="username",
                    autofocus=True,
                    label="Login",
                    prepend_inner_icon="mdi-account",
                )
                LoginTextField(
                    v_model=login_state.name.user_password,
                    autocomplete="current-password",
                    label="Password",
                    type="password",
                    prepend_inner_icon="mdi-lock",
                )
            with v3.VCardActions():
                Button(
                    text="Log In",
                    block=True,
                    color="primary",
                    disabled=("!isValid.value",),
                    loading=(login_state.name.loading,),
                    type="submit",
                )
