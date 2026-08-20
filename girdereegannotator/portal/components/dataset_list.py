from dataclasses import dataclass, field

from trame_server.utils.typed_state import TypedState

from girdereegannotator.database.models import BIDSDataset
from girdereegannotator.utils.load_status import LoadStatus

from .expandable_list import ExpandableList


@dataclass
class DatasetListState:
    current_index: int | None = None
    items: list[BIDSDataset] = field(default_factory=list)
    load_status: LoadStatus = LoadStatus.UNDEFINED
    status_message: str | None = None


class DatasetList(ExpandableList[DatasetListState, BIDSDataset]):
    def __init__(self, list_state: TypedState[DatasetListState], **kwargs) -> None:
        super().__init__(list_state=list_state, item_type="datasets", **kwargs)

        with self.action_slot:
            self.build_select_item_button(text="Open", prepend_icon="mdi-folder")

        with self.expand_slot:
            self.build_metadata(f"{self.item}.metadata")
