from trame_server import Server
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import BIDSDataset, EEGMedia

from .loader_logic import LoaderLogic
from .portal_ui import PortalState, PortalUI


class PortalLogic:
    eeg_media_updated = Signal()

    eeg_media: EEGMedia
    dataset: BIDSDataset

    def __init__(self, server: Server) -> None:
        self.server = server
        self.typed_state = TypedState(self.server.state, PortalState)
        self.typed_state.bind_changes(
            {
                self.typed_state.name.eeg_media_index: self._set_current_eeg_media,
                self.typed_state.name.dataset_index: self._set_current_dataset,
            }
        )
        self.loader_logic = LoaderLogic(server)

    @property
    def name(self) -> PortalState:
        return self.typed_state.name

    @property
    def data(self) -> PortalState:
        return self.typed_state.data

    def reset_state(self) -> None:
        self.typed_state.set_dataclass(PortalState())

    def set_eeg_dataset_list(self) -> None:
        self.data.dataset_list = self.server.controller.list_datasets()

    def set_ui(self, ui: PortalUI) -> None:
        ui.save_annotations_clicked.connect(self._save_annotations)

    def _set_current_dataset(self, dataset_index: int | None) -> None:
        if dataset_index is None:
            self.reset_state()
            self.set_eeg_dataset_list()
            self.dataset = None
            return

        self.dataset = self.data.dataset_list[self.data.dataset_index]
        self.data.eeg_media_list = self.server.controller.list_eeg_media(self.dataset)

    def _update_eeg_media_list(self) -> None:
        self.data.eeg_media_list = [
            self.eeg_media if self.eeg_media.name == eeg_media.name else eeg_media
            for eeg_media in self.data.eeg_media_list
        ]

    def _set_current_eeg_media(self, eeg_media_index: int | None) -> None:
        self.eeg_media_updated()
        if eeg_media_index is None:
            self.eeg_media = None
            return

        self.eeg_media = self.data.eeg_media_list[self.data.eeg_media_index]
        self.loader_logic.load_eeg_media_files(self.eeg_media)

    def _save_annotations(self) -> None:
        self.loader_logic.save_annotations(self.eeg_media)
        self._update_eeg_media_list()
