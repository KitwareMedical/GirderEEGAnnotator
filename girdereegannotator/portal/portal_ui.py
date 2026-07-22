from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import BIDSDataset, EEGMedia

from .loader_ui import LoaderUI


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


class PortalEEGBrowser(html.Div):
    return_clicked = Signal(int)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.typed_state = TypedState(self.state, PortalState)
        with self:
            PortalDatasetList(v_if=f"{self.typed_state.name.dataset_index} == null")
            with html.Div(v_else=True):
                v3.VBtn(icon="mdi-chevron-left", click=f"{self.typed_state.name.dataset_index} = null;")
                PortalEEGList()


class PortalBar(html.Div):
    save_annotations_clicked = Signal()

    def __init__(self, **kwargs) -> None:
        super().__init__(classes="d-flex align-center", style="gap: 8px;", **kwargs)
        self.typed_state = TypedState(self.state, PortalState)
        with self:
            self._build_icon_button(
                click=f"{self.typed_state.name.eeg_media_index} --",
                disabled=(f"!{self.typed_state.name.eeg_media_index}",),
                icon="mdi-chevron-left",
                tooltip="Previous EEG",
            )

            html.Div("Select an EEG", v_if=self.no_eeg_media_selected, classes="font-italic")
            html.Div("{{ " + f"{self.eeg_media}.name" + " }}", v_else=True)

            self._build_icon_button(
                click=f"{self.no_eeg_media_selected} ? {self.typed_state.name.eeg_media_index} = 0 : {self.typed_state.name.eeg_media_index} ++;",
                disabled=(
                    f"{self.typed_state.name.eeg_media_index} === {self.typed_state.name.eeg_media_list}.length - 1 ||"
                    f"!{self.typed_state.name.eeg_media_list}.length",
                ),
                icon="mdi-chevron-right",
                tooltip="Next EEG",
            )
            v3.VSpacer()
            self._build_icon_button(
                icon="mdi-content-save-outline",
                click=self.save_annotations_clicked,
                tooltip="Save annotations",
                disabled=(self.no_eeg_media_selected,),
            )

    @property
    def no_eeg_media_selected(self) -> str:
        return f"{self.typed_state.name.eeg_media_index} == null"

    @property
    def eeg_media(self) -> str:
        return f"{self.typed_state.name.eeg_media_list}.at({self.typed_state.name.eeg_media_index})"

    def _build_icon_button(self, icon: str, tooltip: str | None = None, **kwargs) -> None:
        with v3.VBtn(icon=icon, **kwargs):
            if tooltip is not None:
                v3.VTooltip(
                    text=tooltip,
                    activator="parent",
                    transition="slide-y-transition",
                    location="bottom start",
                )
            v3.VIcon(icon=icon)


class PortalUI:
    save_annotations_clicked = Signal()

    def build_bar(self, **kwargs) -> None:
        bar = PortalBar(**kwargs)
        bar.save_annotations_clicked.connect(self.save_annotations_clicked)

    def build_drawer(self, **kwargs) -> None:
        PortalEEGBrowser(**kwargs)

    def build_loader(self, **kwargs) -> None:
        LoaderUI(**kwargs)
