from trame_server import Server
from undo_stack import Signal

from girdereegannotator.database.models import EEGMedia
from girdereegannotator.eeg_annotator.eeg_viewer_logic import EEGViewerLogic
from girdereegannotator.utils.base_logic import BaseLogic

from .eeg_annotator_ui import EEGAnnotatorState, EGGAnnotatorUI


class EGGAnnotatorLogic(BaseLogic[EEGAnnotatorState]):
    next_clicked = Signal()
    previous_clicked = Signal()
    eeg_media_updated = Signal(EEGMedia)

    def __init__(self, server: Server):
        super().__init__(server, EEGAnnotatorState)

        self.eeg_media = self.typed_state.get_sub_state(self.name.eeg_media)
        self._viewer_logic = EEGViewerLogic(server)

    def load_eeg_media(self, eeg_media: EEGMedia | None) -> None:
        if eeg_media is None:
            self.reset_state()
            return

        self.eeg_media.set_dataclass(eeg_media)
        self._viewer_logic.load_eeg_media_files(self.data.eeg_media)

    def _save_annotations(self) -> None:
        self._viewer_logic.save_annotations(self.data.eeg_media)
        self.eeg_media_updated(self.data.eeg_media)

    def reset_state(self) -> None:
        super().reset_state()
        self._viewer_logic.reset_state()

    def set_ui(self, ui: EGGAnnotatorUI) -> None:
        self._viewer_logic.set_ui(ui.viewer_ui)

        ui.save_annotations_clicked.connect(self._save_annotations)
        ui.previous_clicked.connect(self.previous_clicked)
        ui.next_clicked.connect(self.next_clicked)
