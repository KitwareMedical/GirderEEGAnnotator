from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState

from girdereegannotator.database.models import Dataset
from girdereegannotator.utils.load_status import LoadStatus

from .expandable_list import ExpandableList


@dataclass
class DatasetListState:
    items: list[Dataset] = field(default_factory=list)
    filtered_out_ids: list[str] = field(default_factory=list)
    load_status: LoadStatus = LoadStatus.UNDEFINED
    status_message: str | None = None


class DatasetList(ExpandableList[DatasetListState, Dataset]):
    def __init__(self, item_state: TypedState[Dataset], list_state: TypedState[DatasetListState], **kwargs) -> None:
        super().__init__(item_state=item_state, list_state=list_state, **kwargs)

        with self.action_slot:
            self.build_select_item_button(text="Open", prepend_icon="mdi-folder")

        with self.expand_slot:
            self.build_metadata(f"{self.item}.metadata")

        with self.count_slot:
            self.build_count("datasets")
