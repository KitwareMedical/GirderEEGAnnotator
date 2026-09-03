from asyncio import Task

from trame_server import Server
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import (
    AnnotationsFile,
    AnnotationStatus,
    EEGFileset,
    User,
)
from girdereegannotator.utils.base_logic import BaseLogic

from .eeg_annotator_ui import EEGAnnotatorMode, EEGAnnotatorState, EGGAnnotatorUI
from .eeg_viewer_logic import EEGViewerLogic


class EGGAnnotatorLogic(BaseLogic[EEGAnnotatorState]):
    next_clicked = Signal()
    previous_clicked = Signal()
    eeg_fileset_updated = Signal(EEGFileset)

    def __init__(self, server: Server):
        super().__init__(server, EEGAnnotatorState)

        self._eeg_fileset_state = self.typed_state.get_sub_state(self.name.eeg_fileset)
        self._annotations_file_state = self.typed_state.get_sub_state(self.name.annotations_file)
        self._user_state = TypedState(self.state, User)
        self._viewer_logic = EEGViewerLogic(server)

        self.bind_changes({self.name.eeg_fileset: self._on_eeg_fileset_updated})

    @property
    def eeg_fileset(self) -> EEGFileset:
        return self._eeg_fileset_state.get_dataclass()

    @eeg_fileset.setter
    def eeg_fileset(self, value: EEGFileset) -> None:
        self._eeg_fileset_state.set_dataclass(value)

    @property
    def annotations_file(self) -> AnnotationsFile:
        return self._annotations_file_state.get_dataclass()

    @annotations_file.setter
    def annotations_file(self, value: AnnotationsFile) -> None:
        self._annotations_file_state.set_dataclass(value)

    def _on_eeg_fileset_updated(self, *_args) -> None:
        if self.eeg_fileset._id is not None:
            self.eeg_fileset_updated(self.eeg_fileset)

    def _refresh_annotator_mode(self) -> None:
        mode = EEGAnnotatorMode.UNDEFINED

        if self.eeg_fileset._id is not None:
            if self.eeg_fileset.is_validated:
                mode = EEGAnnotatorMode.DONE

            elif self.annotations_file._id is None or (
                self.annotations_file.status == AnnotationStatus.IN_PROGRESS
                and self.annotations_file.author._id == self._user_state.data._id
            ):
                mode = EEGAnnotatorMode.ANNOTATE

            elif (
                self.annotations_file.status == AnnotationStatus.IN_REVIEW
                and self.annotations_file.author._id != self._user_state.data._id
            ):
                mode = EEGAnnotatorMode.REVIEW

            else:
                mode = EEGAnnotatorMode.READONLY

        self.data.mode = mode

    def _on_task_finished(self, task: Task) -> None:
        eeg_fileset, annotations_file = task.result()
        self.eeg_fileset = eeg_fileset
        self.annotations_file = annotations_file if annotations_file is not None else AnnotationsFile()
        self._refresh_annotator_mode()
        self.state.flush()

    def _on_annotations_file_selected(self, annotations_file: AnnotationsFile | None = None) -> None:
        self.load_eeg_fileset(self.eeg_fileset, annotations_file)

    def load_eeg_fileset(self, eeg_fileset: EEGFileset | None, annotations_file: AnnotationsFile | None) -> None:
        if eeg_fileset is None:
            self.reset_state()
            return

        is_new_eeg_fileset = self.eeg_fileset._id != eeg_fileset._id

        load_task = self._viewer_logic.load_eeg_files(eeg_fileset, annotations_file, is_new_eeg_fileset)
        load_task.add_done_callback(self._on_task_finished)

    def _save_annotations_file(self) -> None:
        save_task = self._viewer_logic.save_annotations_file(self.eeg_fileset)
        save_task.add_done_callback(self._on_task_finished)

    def reset_state(self) -> None:
        super().reset_state()
        self._viewer_logic.reset_state()

    def set_ui(self, ui: EGGAnnotatorUI) -> None:
        self._viewer_logic.set_ui(ui.viewer_ui)

        ui.previous_clicked.connect(self.previous_clicked)
        ui.next_clicked.connect(self.next_clicked)
        ui.annotation_selected.connect(self._on_annotations_file_selected)
        ui.annotation_saved.connect(self._save_annotations_file)
