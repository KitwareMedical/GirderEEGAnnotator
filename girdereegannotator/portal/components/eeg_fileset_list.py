from dataclasses import dataclass, field

from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState

from girdereegannotator.database.models import EEGFileset
from girdereegannotator.utils.load_status import LoadStatus

from .expandable_list import ExpandableList


@dataclass
class EEGFilesetListState:
    items: list[EEGFileset] = field(default_factory=list)
    excluded_ids: list[str] = field(default_factory=list)
    load_status: LoadStatus = LoadStatus.UNDEFINED
    status_message: str | None = None


class EEGFilesetList(ExpandableList[EEGFilesetListState, EEGFileset]):
    def __init__(
        self, item_state: TypedState[EEGFileset], list_state: TypedState[EEGFilesetListState], **kwargs
    ) -> None:
        super().__init__(item_state=item_state, list_state=list_state, **kwargs)

        with self.action_slot:
            v3.VChip(
                v_if=f"{self.item}.annotations.length",
                append_icon="mdi-tag",
                text=(f"{self.item}.annotations.length",),
                color="warning",
            )
            self.build_select_item_button(text="View", prepend_icon="mdi-eye-outline")

        with self.expand_slot:
            self.build_metadata(f"{self.item}.metadata")

        with self.count_slot:
            self.build_count("EEG filesets")
