from trame_server import Server
from undo_stack import Signal

from girdereegannotator.database.models import EEGFileset
from girdereegannotator.eeg_annotator.eeg_viewer_logic import EEGViewerLogic
from girdereegannotator.utils.base_logic import BaseLogic

from .eeg_annotator_ui import EEGAnnotatorState, EGGAnnotatorUI


class EGGAnnotatorLogic(BaseLogic[EEGAnnotatorState]):
    next_clicked = Signal()
    previous_clicked = Signal()
    eeg_fileset_updated = Signal(EEGFileset)

    def __init__(self, server: Server):
        super().__init__(server, EEGAnnotatorState)

        self.eeg_fileset = self.typed_state.get_sub_state(self.name.eeg_fileset)
        self._viewer_logic = EEGViewerLogic(server)

    def load_eeg_fileset(self, eeg_fileset: EEGFileset | None) -> None:
        if eeg_fileset is None:
            self.reset_state()
            return

        self.eeg_fileset.set_dataclass(eeg_fileset)
        self._viewer_logic.load_eeg_files(self.data.eeg_fileset)

    def _save_annotations(self) -> None:
        eeg_fileset = self.eeg_fileset.get_dataclass()
        self._viewer_logic.save_annotations(eeg_fileset)

        # Update state with latest annotations
        self.eeg_fileset.set_dataclass(eeg_fileset)
        self.eeg_fileset_updated(eeg_fileset)

    def reset_state(self) -> None:
        super().reset_state()
        self._viewer_logic.reset_state()

    def set_ui(self, ui: EGGAnnotatorUI) -> None:
        self._viewer_logic.set_ui(ui.viewer_ui)

        ui.save_annotations_clicked.connect(self._save_annotations)
        ui.previous_clicked.connect(self.previous_clicked)
        ui.next_clicked.connect(self.next_clicked)
