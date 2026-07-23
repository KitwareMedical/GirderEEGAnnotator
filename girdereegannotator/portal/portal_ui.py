from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState

from girdereegannotator.database.models import BIDSDataset, EEGMedia


@dataclass
class PortalState:
    dataset_index: int | None = None
    dataset_list: list[BIDSDataset] = field(default_factory=list)
    eeg_media_index: int | None = None
    eeg_media_list: list[EEGMedia] = field(default_factory=list)


class PortalEEGList(v3.VList):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.typed_state = TypedState(self.state, PortalState)
        with self:
            v3.VListItem(
                v_for=f"(eeg_media, index) in {self.typed_state.name.eeg_media_list}",
                active=(f"{self.typed_state.name.eeg_media_index} === index",),
                title=("eeg_media.name",),
                click=f"{self.typed_state.name.eeg_media_index} = index",
            )


class PortalDatasetList(v3.VList):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.typed_state = TypedState(self.state, PortalState)
        with self:
            v3.VListItem(
                v_for=f"(dataset, index) in {self.typed_state.name.dataset_list}",
                title=("dataset.name",),
                click=f"{self.typed_state.name.dataset_index} = index",
            )


class PortalUI(html.Div):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.typed_state = TypedState(self.state, PortalState)
        with self:
            PortalDatasetList(v_if=f"{self.typed_state.name.dataset_index} == null")
            with html.Div(v_else=True):
                v3.VBtn(icon="mdi-chevron-left", click=f"{self.typed_state.name.dataset_index} = null;")
                PortalEEGList()
