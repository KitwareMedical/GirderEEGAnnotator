from dataclasses import dataclass

from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.utils.components import Button


@dataclass
class SearchState:
    search_text: str | None = None


class SearchFilter(v3.VForm):
    def __init__(self, search_state: TypedState[SearchState], on_search_clicked: Signal, **kwargs) -> None:
        super().__init__(
            classes="search-input",
            submit_prevent=on_search_clicked,
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
                hide_details=True,
                clearable=True,
                click_clear=on_search_clicked,
            )
            Button(
                color="secondary",
                density="comfortable",
                icon="mdi-magnify",
                type="submit",
            )
