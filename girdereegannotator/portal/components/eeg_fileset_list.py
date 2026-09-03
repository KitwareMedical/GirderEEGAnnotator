from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import (
    AnnotationsFile,
    AnnotationStatus,
    EEGFileset,
)
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
    annotation_selected = Signal(EEGFileset, AnnotationsFile)
    annotation_deleted = Signal(AnnotationsFile)

    def _count_annotation_per_status(self, annotation_status: AnnotationStatus) -> str:
        return f"{self.item}.annotations_files.filter(f => f.status === {annotation_status.value}).length"

    def _build_annotation_status_chip(self, annotation_status: AnnotationStatus, **kwargs) -> None:
        annotations_count = self._count_annotation_per_status(annotation_status)
        v3.VChip(
            v_if=annotations_count,
            text=(annotations_count,),
            **kwargs,
        )

    def __init__(
        self, item_state: TypedState[EEGFileset], list_state: TypedState[EEGFilesetListState], **kwargs
    ) -> None:
        super().__init__(item_state=item_state, list_state=list_state, **kwargs)

        with self.action_slot:
            self._build_annotation_status_chip(
                AnnotationStatus.IN_PROGRESS, color="warning", append_icon="mdi-tag-edit"
            )
            self._build_annotation_status_chip(AnnotationStatus.IN_REVIEW, color="info", append_icon="mdi-tag-arrow-up")
            self._build_annotation_status_chip(AnnotationStatus.DONE, color="success", append_icon="mdi-tag-check")

            self.build_select_item_button(text="View", prepend_icon="mdi-eye-outline")

        with self.expand_slot:
            html.Div("Annotations", classes="text-secondary text-subtitle-1")
            annotation_list = AnnotationList(item_state)
            self._connect_annotation_list(annotation_list)

            v3.VDivider()

            html.Div("Metadata", classes="text-secondary text-subtitle-1")
            self.build_metadata(
                f"{self.item}.metadata",
            )

        with self.count_slot:
            self.build_count("EEG filesets")

    def select_annotations_file(self, annotation_id: str) -> None:
        eeg_fileset = self.item_state.get_dataclass()
        annotation = next((ann for ann in eeg_fileset.annotations_files if ann._id == annotation_id), None)
        self.annotation_selected(eeg_fileset, annotation)

    def create_new_annotation(self) -> None:
        eeg_fileset = self.item_state.get_dataclass()
        self.item_selected(eeg_fileset)

    def delete_annotation(self, annotation_id: str) -> None:
        eeg_fileset = self.item_state.get_dataclass()
        annotation = next((ann for ann in eeg_fileset.annotations_files if ann._id == annotation_id), None)
        self.annotation_deleted(annotation)

    def _connect_annotation_list(self, annotation_list: AnnotationList) -> None:
        annotation_list.new_annotation_clicked.connect(self.create_new_annotation)
        annotation_list.annotation_selected.connect(self.select_annotations_file)
        annotation_list.delete_clicked.connect(self.delete_annotation)
