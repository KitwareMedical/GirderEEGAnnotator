from dataclasses import dataclass, field
from enum import Enum, auto

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from undo_stack import Signal

from girdereegannotator.database.models import (
    AnnotationsFile,
    AnnotationStatus,
    EEGFileset,
)
from girdereegannotator.utils.base_ui import BaseUI

from .components import (
    AnnotateActions,
    AnnotationInput,
    FilesetInput,
    NoAction,
    ReadonlyAction,
    ReviewActions,
    ShortcutsPanel,
)
from .eeg_viewer_ui import EEGViewerUI


class EEGAnnotatorMode(Enum):
    UNDEFINED = auto()
    READONLY = auto()
    ANNOTATE = auto()
    REVIEW = auto()
    DONE = auto()


@dataclass
class EEGAnnotatorState:
    eeg_fileset: EEGFileset = field(default_factory=EEGFileset)
    annotations_file: AnnotationsFile = field(default_factory=AnnotationsFile)
    mode: EEGAnnotatorMode = EEGAnnotatorMode.UNDEFINED


class EGGAnnotatorUI(html.Div, BaseUI[EEGAnnotatorState]):
    previous_clicked = Signal()
    next_clicked = Signal()
    annotation_selected = Signal(AnnotationsFile | None)
    annotation_saved = Signal()
    annotation_status_changed = Signal(AnnotationStatus)
    annotation_deleted = Signal()

    def __init__(self, **kwargs) -> None:
        super().__init__(classes="annotator", **kwargs)
        self._init_typed_state(self.state, EEGAnnotatorState)

        with self:
            self.viewer_ui = EEGViewerUI()

    def build_toolbar(self) -> None:
        v3.VSpacer()

        with html.Div(classes="annotator-tool"):
            html.Label("EEG", classes="annotator-tool__label")
            with html.Div(classes="annotator-tool__content"):
                fileset_input = FilesetInput()
                self._connect_fileset_input(fileset_input)

        v3.VSpacer()

        with html.Div(classes="annotator-tool"):
            html.Label("Annotations", classes="annotator-tool__label")
            with html.Div(classes="annotator-tool__content"), html.Div(classes="d-flex align-center fill-height"):
                annotation_input = AnnotationInput(
                    annotations_file_state=self.get_sub_state(self.name.annotations_file),
                    eeg_fileset_state=self.get_sub_state(self.name.eeg_fileset),
                    eeg_fileset_validated=self._is_annotator_mode(EEGAnnotatorMode.DONE),
                )
                self._connect_annotation_input(annotation_input)
                v3.VDivider(vertical=True)
                annotate_actions = AnnotateActions(v_if=self._is_annotator_mode(EEGAnnotatorMode.ANNOTATE))
                review_actions = ReviewActions(v_else_if=self._is_annotator_mode(EEGAnnotatorMode.REVIEW))
                ReadonlyAction(
                    v_else_if=f"{self._is_annotator_mode(EEGAnnotatorMode.READONLY)} || {self._is_annotator_mode(EEGAnnotatorMode.DONE)}"
                )
                NoAction(v_else=True)

                self._connect_annotate_actions(annotate_actions)
                self._connect_review_actions(review_actions)

        v3.VSpacer()

        ShortcutsPanel()

    def _is_annotator_mode(self, annotator_mode: EEGAnnotatorMode) -> str:
        return f"({self.name.mode} === {annotator_mode.value})"

    def _connect_fileset_input(self, fileset_input: FilesetInput) -> None:
        fileset_input.next_fileset_clicked.connect(self.next_clicked)
        fileset_input.previous_fileset_clicked.connect(self.previous_clicked)

    def _connect_annotation_input(self, annotation_input: AnnotationInput) -> None:
        annotation_input.annotation_selected.connect(self.annotation_selected)

    def _connect_annotate_actions(self, annotate_actions: AnnotateActions) -> None:
        annotate_actions.annotation_submitted.connect(
            lambda: self.annotation_status_changed(AnnotationStatus.IN_REVIEW)
        )
        annotate_actions.annotation_saved.connect(self.annotation_saved)
        annotate_actions.annotation_deleted.connect(self.annotation_deleted)

    def _connect_review_actions(self, review_actions: ReviewActions) -> None:
        review_actions.annotation_approved.connect(lambda: self.annotation_status_changed(AnnotationStatus.DONE))
        review_actions.annotation_rejected.connect(lambda: self.annotation_status_changed(AnnotationStatus.IN_PROGRESS))
