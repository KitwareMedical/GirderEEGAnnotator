from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import EEGMedia, EEGMediaMetadata

from .loader_ui import LoaderUI


@dataclass
class PortalState:
    eeg_media: EEGMedia = field(default_factory=EEGMedia)
    eeg_media_list: list[EEGMedia] = field(default_factory=list)


class PortalEEGList(v3.VList):
    def __init__(self, select_callable: Callable, **kwargs) -> None:
        super().__init__(**kwargs)
        self.typed_state = TypedState(self.state, PortalState)
        with self:
            v3.VListItem(
                v_for=f"eeg_media in {self.typed_state.name.eeg_media_list}",
                active=(f"{self.typed_state.name.eeg_media._id} === eeg_media._id",),
                value=("eeg_media",),
                title=("eeg_media.name",),
                click=(select_callable, "[eeg_media]"),
            )


class PortalBar(html.Div):
    def __init__(
        self,
        previous_select_callable: Callable,
        next_select_callable: Callable,
        save_annotations_callable: Callable,
        **kwargs,
    ) -> None:
        super().__init__(classes="d-flex align-center", style="gap: 8px;", **kwargs)
        self.typed_state = TypedState(self.state, PortalState)
        with self:
            self._build_icon_button(
                icon="mdi-chevron-left",
                click=previous_select_callable,
                tooltip="Previous EEG",
            )
            html.Div("{{ " + self.typed_state.name.eeg_media.name + " }}", v_if=(self.typed_state.name.eeg_media.name,))
            html.Div("Select an EEG", v_else=True, classes="font-italic")
            self._build_icon_button(
                icon="mdi-chevron-right",
                click=next_select_callable,
                tooltip="Next EEG",
            )
            v3.VSpacer()
            self._build_icon_button(
                icon="mdi-content-save-outline",
                click=save_annotations_callable,
                tooltip="Save annotations",
                disabled=(f"!{self.typed_state.name.eeg_media.name}",),
            )

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
    eeg_media_selected = Signal(EEGMedia)
    save_annotations_clicked = Signal()
    previous_eeg_clicked = Signal()
    next_eeg_clicked = Signal()

    def _select_eeg_media(self, eeg_media_dict: dict[str, Any]) -> None:
        eeg_media_dict["meta"] = EEGMediaMetadata(**eeg_media_dict["meta"])
        eeg_media = EEGMedia(**eeg_media_dict)
        self.eeg_media_selected(eeg_media)

    def build_bar(self, **kwargs) -> None:
        PortalBar(self.previous_eeg_clicked, self.next_eeg_clicked, self.save_annotations_clicked, **kwargs)

    def build_drawer(self, **kwargs) -> None:
        PortalEEGList(self._select_eeg_media, **kwargs)

    def build_loader(self, **kwargs) -> None:
        LoaderUI(**kwargs)
