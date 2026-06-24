from trame_rca.utils import RcaViewAdapter
from trame_server import Server
from trame_server.utils.typed_state import TypedState

from .eeg_annotator_ui import EEGAnnotatorState, EGGAnnotatorUI
from .eeg_annotator_window import EGGAnnotatorWindow


class EGGAnnotatorLogic:
    view_handler: RcaViewAdapter

    def __init__(self, server: Server):
        self.server = server
        self.typed_state = TypedState(self.server.state, EEGAnnotatorState)
        self.eeg_window = EGGAnnotatorWindow()

    def set_ui(self, ui: EGGAnnotatorUI) -> None:
        self.view_handler = ui.rca.create_view_handler(self.eeg_window)

    def set_file_path(self, file_path: str) -> None:
        try:
            self.eeg_window.set_file_path(file_path)
            self.view_handler.update_size(None, self.eeg_window.window_size)
            self.typed_state.data.load_error = None

        except Exception as e:
            self.typed_state.data.load_error = f"Could not load data into EEG Annotator: {e}"
