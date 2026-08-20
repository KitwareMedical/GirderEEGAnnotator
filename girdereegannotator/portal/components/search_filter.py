from dataclasses import dataclass

from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.utils.components import Button


@dataclass
class SearchState:
    search_text: str | None = None


class Search(v3.VForm):
    search_clicked = Signal()

    def __init__(self, search_state: TypedState[SearchState], **kwargs) -> None:
        super().__init__(
            classes="search-input",
            submit_prevent=self.search_clicked,
            __events=[("submit_prevent", "submit.prevent")],
            **kwargs,
        )

        with self:
            v3.VTextField(
                v_model=(search_state.name.search_text,),
                placeholder="Search by name",
                variant="solo",
                flat=True,
                density="comfortable",
                width=200,
                hide_details=True,
                clearable=True,
                click_clear=self.search_clicked,
            )
            Button(
                color="secondary",
                density="comfortable",
                icon="mdi-magnify",
                type="submit",
            )
