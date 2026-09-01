from trame.widgets import html
from trame.widgets import vuetify3 as v3
from undo_stack import Signal

from girdereegannotator.utils.components import Button


class FilesetInput(html.Div):
    next_fileset_clicked = Signal()
    previous_fileset_clicked = Signal()

    def __init__(self, **kwargs) -> None:
        super().__init__(classes="fileset-input", **kwargs)

        with self:
            Button(
                click=self.previous_fileset_clicked,
                icon="mdi-chevron-left",
                tooltip="Previous EEG",
                tooltip_location="bottom start",
                density="comfortable",
            )
            v3.VDivider(vertical=True)
            Button(
                click=self.next_fileset_clicked,
                icon="mdi-chevron-right",
                tooltip="Next EEG",
                tooltip_location="bottom start",
                density="comfortable",
            )
