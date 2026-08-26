from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from undo_stack import Signal

from girdereegannotator.database.models import EEGFileset
from girdereegannotator.utils.base_ui import BaseUI
from girdereegannotator.utils.components import Button

from .components.shortcuts_panel import ShortcutsPanel
from .eeg_viewer_ui import EEGViewerUI


@dataclass
class EEGAnnotatorState:
    eeg_fileset: EEGFileset = field(default_factory=EEGFileset)


class EGGAnnotatorUI(html.Div, BaseUI[EEGAnnotatorState]):
    previous_clicked = Signal()
    next_clicked = Signal()
    save_clicked = Signal()

    def __init__(self, **kwargs) -> None:
        super().__init__(classes="fill-height", **kwargs)
        self._init_typed_state(self.state, EEGAnnotatorState)

        with self:
            self.viewer_ui = EEGViewerUI(style="height: calc(100% - 50px);")

            with html.Div(classes="d-flex align-center justify-center", style="height: 50px;", **kwargs):
                Button(
                    click=self.previous_clicked,
                    icon="mdi-chevron-left",
                    tooltip="Previous EEG",
                    tooltip_location="bottom start",
                )
                Button(
                    click=self.next_clicked,
                    icon="mdi-chevron-right",
                    tooltip="Next EEG",
                    tooltip_location="bottom start",
                )
                v3.VSpacer()

                html.Div(
                    "{{ " + self.typed_state.name.eeg_fileset.name + " }}", v_if=self.typed_state.name.eeg_fileset.name
                )

                v3.VSpacer()
                Button(
                    icon="mdi-content-save-outline",
                    click=self.save_clicked,
                    tooltip="Save annotations",
                    tooltip_location="bottom start",
                )
                ShortcutsPanel()
