from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import User
from girdereegannotator.utils.components import Button


class UserProfileMenu(v3.VMenu):
    logout_clicked = Signal()

    def __init__(self, **kwargs):
        super().__init__(
            close_on_content_click=False,
            scrim=True,
            location="end",
            offset=10,
            **kwargs,
        )

        user_state = TypedState(self.state, User)

        with self:
            with v3.Template(v_slot_activator="{ props : activatorProps }"):
                Button(
                    v_bind="activatorProps",
                    avatar_text=f"{{{{ {user_state.name.first_name}.charAt(0) }}}}{{{{ {user_state.name.last_name}.charAt(0) }}}}",
                    text_transform="uppercase",
                    color="secondary",
                )

            with (
                v3.VCard(
                    title=("`${ " + user_state.name.first_name + " } ${ " + user_state.name.last_name + " }`",),
                    subtitle=(user_state.name.login,),
                ),
                v3.VCardActions(),
            ):
                Button(
                    text="Log Out",
                    block=True,
                    click=self.logout_clicked,
                    color="error",
                )
