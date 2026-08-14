from dataclasses import dataclass

from trame_server.utils.typed_state import TypedState

from girdereegannotator.database.models import BIDSDataset

from .expandable_list import ExpandableList, ExpandableListState


@dataclass
class DatasetListState(ExpandableListState[BIDSDataset]): ...


class DatasetList(ExpandableList[DatasetListState, BIDSDataset]):
    def __init__(self, list_state: TypedState[DatasetListState], **kwargs) -> None:
        super().__init__(list_state, **kwargs)

        with self.action_slot:
            self.build_select_item_button(icon="mdi-arrow-right")

        with self.expand_slot:
            self.build_metadata(f"{self.item}.metadata")
