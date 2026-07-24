from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import User


class UserProfileMenu(v3.VMenu):
    logout_clicked = Signal()

    def __init__(self, user_state: TypedState[User], **kwargs):
        super().__init__(
            close_on_content_click=False,
            scrim=True,
            location="end",
            offset=10,
            **kwargs,
        )
        with self:
            with (
                v3.Template(v_slot_activator="{ props : activatorProps }"),
                v3.VBtn(v_bind="activatorProps", icon=True, variant="text"),
                v3.VAvatar(),
            ):
                html.Span(
                    f"{{{{ {user_state.name.first_name}.charAt(0) }}}}{{{{ {user_state.name.last_name}.charAt(0) }}}}",
                    classes="text-uppercase",
                )

            with (
                v3.VCard(
                    title=("`${ " + user_state.name.first_name + " } ${ " + user_state.name.last_name + " }`",),
                    subtitle=(user_state.name.login,),
                ),
                v3.VCardActions(),
            ):
                v3.VBtn(
                    text="Log Out",
                    block=True,
                    click=self.logout_clicked,
                    color="error",
                    variant="flat",
                )
