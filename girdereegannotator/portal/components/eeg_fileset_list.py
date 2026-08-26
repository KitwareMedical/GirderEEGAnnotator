from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState

from girdereegannotator.database.models import EEGFileset
from girdereegannotator.utils.load_status import LoadStatus

from .eeg_annotation_list import AnnotationList
from .expandable_list import ExpandableList


@dataclass
class EEGFilesetListState:
    items: list[EEGFileset] = field(default_factory=list)
    filtered_out_ids: list[str] = field(default_factory=list)
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
            html.Div("Annotations", classes="text-secondary text-subtitle-1")
            AnnotationList(
                eeg_id=self.item_state.name._id,
                annotations=f"{self.item}.annotations",
                select_callable=self.select_item,
            )

            v3.VDivider()

            html.Div("Metadata", classes="text-secondary text-subtitle-1")
            self.build_metadata(
                f"{self.item}.metadata",
            )

        with self.count_slot:
            self.build_count("EEG filesets")

    def select_item(self, eeg_fileset_id: str, annotation_id: str | None = None) -> None:
        eeg_fileset = next(it for it in self.list_state.data.items if it._id == eeg_fileset_id)
        annotation = next((ann for ann in eeg_fileset.annotations if ann._id == annotation_id), None)
        self.item_selected(eeg_fileset, annotation)
