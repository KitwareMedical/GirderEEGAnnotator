from dataclasses import dataclass, field
from typing import Any

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.core import Server
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import EEGMedia, EEGMediaFile, EEGMediaMetadata


@dataclass
class LoaderState:
    eeg_loading: bool = False
    eeg_file: EEGMediaFile = field(default_factory=EEGMediaFile)
    eeg_annotation_file: EEGMediaFile = field(default_factory=EEGMediaFile)


@dataclass
class PortalState:
    eeg_media: EEGMedia = field(default_factory=EEGMedia)
    eeg_media_list: list[EEGMedia] = field(default_factory=list)


class PortalUI:
    eeg_media_selected = Signal(EEGMedia)
    save_annotations_clicked = Signal()
    approve_annotations_clicked = Signal()
    previous_eeg_clicked = Signal()
    next_eeg_clicked = Signal()

    def __init__(self, server: Server):
        self.server = server
        self.portal_state = TypedState(server.state, PortalState)
        self.loader_state = TypedState(server.state, LoaderState)

    def _build_icon_button(self, icon: str, tooltip: str | None = None, **kwargs) -> None:
        with v3.VBtn(**kwargs):
            if tooltip is not None:
                v3.VTooltip(
                    text=tooltip,
                    activator="parent",
                    transition="slide-y-transition",
                    location="bottom start",
                )
            v3.VIcon(icon=icon)

    def _select_eeg_media(self, eeg_media_dict: dict[str, Any]) -> None:
        eeg_media_dict["meta"] = EEGMediaMetadata(**eeg_media_dict["meta"])
        eeg_media = EEGMedia(**eeg_media_dict)
        self.eeg_media_selected(eeg_media)

    def build_bar(self) -> None:
        self._build_icon_button(
            icon="mdi-content-save-outline",
            click=self.save_annotations_clicked,
            tooltip="Save annotations",
            disabled=(f"!{self.portal_state.name.eeg_media.name}",),
        )
        v3.VSpacer()
        self._build_icon_button(
            icon="mdi-chevron-left",
            click=self.previous_eeg_clicked,
            tooltip="Previous EEG",
        )
        html.Div("{{ " + self.portal_state.name.eeg_media.name + " }}", classes="px-2")
        self._build_icon_button(
            icon="mdi-chevron-right",
            click=self.next_eeg_clicked,
            tooltip="Next EEG",
        )
        v3.VSpacer()

    def build_drawer(self) -> None:
        with (
            v3.VList(),
            v3.VListItem(
                v_for=f"eeg_media in {self.portal_state.name.eeg_media_list}",
                active=(f"{self.portal_state.name.eeg_media._id} === eeg_media._id",),
                value=("eeg_media",),
                title=("eeg_media.name",),
                # Make sure eeg viewer takes the focus after loading
                click=(
                    "trigger('"
                    f"{self.server.controller.trigger_name(self._select_eeg_media)}"
                    "', [eeg_media]).then(() => { trame.refs.eegview.$refs.rootElem.focus(); })"
                ),
            ),
            v3.Template(v_slot_append="{ isActive }"),
        ):
            v3.VProgressCircular(
                v_if=(f"isActive && {self.loader_state.name.eeg_loading}",),
                indeterminate=True,
                size=15,
            )
