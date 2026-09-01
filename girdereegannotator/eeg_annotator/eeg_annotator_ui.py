from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from undo_stack import Signal

from girdereegannotator.database.models import AnnotationsFile, EEGFileset
from girdereegannotator.utils.base_ui import BaseUI

from .components import AnnotationInput, FilesetInput, ShortcutsPanel
from .eeg_viewer_ui import EEGViewerUI


@dataclass
class EEGAnnotatorState:
    eeg_fileset: EEGFileset = field(default_factory=EEGFileset)
    annotations_file: AnnotationsFile = field(default_factory=AnnotationsFile)


class EGGAnnotatorUI(html.Div, BaseUI[EEGAnnotatorState]):
    previous_clicked = Signal()
    next_clicked = Signal()
    annotation_saved = Signal()
    annotation_selected = Signal(AnnotationsFile | None)

    def __init__(self, **kwargs) -> None:
        super().__init__(classes="annotator", **kwargs)
        self._init_typed_state(self.state, EEGAnnotatorState)

        with self:
            self.viewer_ui = EEGViewerUI()

    def build_toolbar(self) -> None:
        v3.VSpacer()

        with html.Div(classes="annotator-tool"):
            html.Label("EEG fileset", classes="annotator-tool__label")
            with html.Div(classes="annotator-tool__content"):
                fileset_input = FilesetInput()
                self._connect_fileset_input(fileset_input)

        v3.VSpacer()

        with html.Div(classes="annotator-tool"):
            html.Label("Annotations file", classes="annotator-tool__label")
            with html.Div(classes="annotator-tool__content"):
                annotation_input = AnnotationInput(
                    annotations_file_state=self.get_sub_state(self.name.annotations_file),
                    eeg_fileset_state=self.get_sub_state(self.name.eeg_fileset),
                )
                self._connect_annotation_input(annotation_input)

        v3.VSpacer()

        ShortcutsPanel()

    def _connect_fileset_input(self, fileset_input: FilesetInput) -> None:
        fileset_input.next_fileset_clicked.connect(self.next_clicked)
        fileset_input.previous_fileset_clicked.connect(self.previous_clicked)

    def _connect_annotation_input(self, annotation_input: AnnotationInput) -> None:
        annotation_input.annotation_selected.connect(self.annotation_selected)
        annotation_input.annotation_saved.connect(self.annotation_saved)
