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

from .eeg_annotator_state import EEGAnnotatorMode, EEGAnnotatorState
from .eeg_annotator_ui import EGGAnnotatorUI
from .eeg_viewer_logic import EEGViewerLogic


class EGGAnnotatorLogic(BaseLogic[EEGAnnotatorState]):
    next_clicked = Signal()
    previous_clicked = Signal()
    eeg_fileset_updated = Signal(EEGFileset)

    def __init__(self, server: Server):
        super().__init__(server, EEGAnnotatorState)

        self.eeg_fileset = self.typed_state.get_sub_state(self.name.eeg_fileset)
        self.annotations_file = self.typed_state.get_sub_state(self.name.annotations_file)
        self.current_user = TypedState(self.state, User)
        self._viewer_logic = EEGViewerLogic(server)

    def _upsert_annotations_file(self, new_annotations_file: AnnotationsFile) -> None:
        if any(ann._id == new_annotations_file._id for ann in self.data.eeg_fileset.annotations_files):
            self.data.eeg_fileset.annotations_files = [
                new_annotations_file if ann._id == new_annotations_file._id else ann
                for ann in self.data.eeg_fileset.annotations_files
            ]
        self.data.eeg_fileset.annotations_files = [*self.data.eeg_fileset.annotations_files, new_annotations_file]

    def _refresh_eeg_fileset(self) -> None:
        eeg_fileset = self.eeg_fileset.get_dataclass()
        refreshed_eeg_fileset = self.ctrl.refresh_eeg_fileset(eeg_fileset)
        self.eeg_fileset.set_dataclass(refreshed_eeg_fileset)

        self._refresh_annotator_mode()

    def _refresh_annotator_mode(self, *_args) -> None:
        updated_eeg_fileset = self.eeg_fileset.get_dataclass()
        updated_annotations_file = self.annotations_file.get_dataclass()

        mode = EEGAnnotatorMode.UNDEFINED

        if updated_eeg_fileset._id is not None:
            self.eeg_fileset_updated(updated_eeg_fileset)

            if updated_eeg_fileset.is_validated:
                mode = EEGAnnotatorMode.DONE

            elif updated_annotations_file._id is None or (
                updated_annotations_file.status == AnnotationStatus.IN_PROGRESS
                and updated_annotations_file.author._id == self.current_user.data._id
            ):
                mode = EEGAnnotatorMode.ANNOTATE

            elif (
                updated_annotations_file.status == AnnotationStatus.IN_REVIEW
                and updated_annotations_file.author._id != self.current_user.data._id
            ):
                mode = EEGAnnotatorMode.REVIEW

            else:
                mode = EEGAnnotatorMode.READONLY

        self.data.mode = mode

    def _on_load_task_finished(self, task: Task) -> None:
        eeg_fileset, annotations_file = task.result()
        self.eeg_fileset.set_dataclass(eeg_fileset)
        self.annotations_file.set_dataclass(annotations_file if annotations_file is not None else AnnotationsFile())
        self._refresh_annotator_mode()
        self.state.flush()

    def _on_annotations_file_selected(self, annotations_file: AnnotationsFile | None = None) -> None:
        self.load_eeg_fileset(self.eeg_fileset.get_dataclass(), annotations_file)

    def load_eeg_fileset(self, eeg_fileset: EEGFileset | None, annotations_file: AnnotationsFile | None) -> None:
        if eeg_fileset is None:
            self.reset_state()
            return

        is_new_eeg_fileset = self.eeg_fileset.data._id != eeg_fileset._id

        load_task = self._viewer_logic.load_eeg_files(eeg_fileset, annotations_file, is_new_eeg_fileset)
        load_task.add_done_callback(self._on_load_task_finished)

    def _save_annotations_file(self) -> None:
        self._refresh_eeg_fileset()
        annotations_file = self._viewer_logic.save_annotations_file(self.data.eeg_fileset)
        self._upsert_annotations_file(annotations_file)
        self.annotations_file.set_dataclass(annotations_file)

    def reset_state(self) -> None:
        super().reset_state()
        self._viewer_logic.reset_state()

    def set_ui(self, ui: EGGAnnotatorUI) -> None:
        self._viewer_logic.set_ui(ui.viewer_ui)

        ui.annotation_saved.connect(self._save_annotations_file)
        ui.previous_clicked.connect(self.previous_clicked)
        ui.next_clicked.connect(self.next_clicked)
        ui.annotation_selected.connect(self._on_annotations_file_selected)
