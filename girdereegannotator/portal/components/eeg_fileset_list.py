from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState

from girdereegannotator.database.models import EEGFileset

from .expandable_list import ExpandableList


@dataclass
class EEGFilesetListState:
    current_index: int | None = None
    items: list[EEGFileset] = field(default_factory=list)


class EEGFilesetList(ExpandableList[EEGFilesetListState, EEGFileset]):
    def __init__(self, list_state: TypedState[EEGFilesetListState], **kwargs) -> None:
        super().__init__(list_state, **kwargs)

        with self.action_slot:
            v3.VChip(
                v_if=f"{self.item}.annotations.length",
                append_icon="mdi-tag",
                text=(f"{self.item}.annotations.length",),
                color="warning",
            )
            self.build_select_item_button(icon="mdi-cast-variant")

        with self.expand_slot:
            html.Span("Metadata")
