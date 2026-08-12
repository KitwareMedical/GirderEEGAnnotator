from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from undo_stack import Signal

from girdereegannotator.database.models import EEGMedia
from girdereegannotator.utils.base_ui import BaseUI

from .components.shortcuts_panel import ShortcutsPanel
from .eeg_viewer_ui import EEGViewerUI


@dataclass
class EEGAnnotatorState:
    eeg_media: EEGMedia = field(default_factory=EEGMedia)


class EGGAnnotatorUI(html.Div, BaseUI[EEGAnnotatorState]):
    previous_clicked = Signal()
    next_clicked = Signal()
    save_annotations_clicked = Signal()

    def __init__(self, **kwargs) -> None:
        super().__init__(classes="fill-height", **kwargs)
        self._init_typed_state(self.state, EEGAnnotatorState)

        with self:
            self.viewer_ui = EEGViewerUI(style="height: calc(100% - 50px);")

            with html.Div(classes="d-flex align-center justify-center", style="height: 50px;", **kwargs):
                self._build_icon_button(
                    click=self.previous_clicked,
                    icon="mdi-chevron-left",
                    tooltip="Previous EEG",
                )
                self._build_icon_button(
                    click=self.next_clicked,
                    icon="mdi-chevron-right",
                    tooltip="Next EEG",
                )
                v3.VSpacer()

                html.Div(
                    "{{ " + self.typed_state.name.eeg_media.name + " }}", v_if=self.typed_state.name.eeg_media.name
                )

                v3.VSpacer()
                self._build_icon_button(
                    icon="mdi-content-save-outline",
                    click=self.save_annotations_clicked,
                    tooltip="Save annotations",
                )
                ShortcutsPanel()

    def _build_icon_button(self, icon: str, tooltip: str | None = None, **kwargs) -> None:
        with v3.VBtn(icon=icon, variant="text", **kwargs):
            if tooltip is not None:
                v3.VTooltip(
                    text=tooltip,
                    activator="parent",
                    transition="slide-y-transition",
                    location="bottom start",
                )
            v3.VIcon(icon=icon)
