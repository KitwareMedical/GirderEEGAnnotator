from trame.widgets import html
from trame.widgets import vuetify3 as v3
from undo_stack import Signal

from girdereegannotator.utils.components import Button


class AnnotationList(v3.VList):
    def __init__(self, eeg_id: str, annotations: str, select_callable: Signal, **kwargs) -> None:
        super().__init__(**kwargs)

        with self:
            with html.Div(v_for=f"annotation in {annotations}"):
                v3.VListItem(
                    click=(select_callable, f"[{eeg_id}, annotation._id]"),
                    title=("annotation.name",),
                )
                v3.VDivider(v_if=f"annotation_index + 1 < {annotations}.length", classes="mx-4")

            with html.Div(classes="d-flex justify-center"):
                Button(
                    click=(select_callable, f"[{eeg_id}]"),
                    variant="flat",
                    color="primary",
                    prepend_icon="mdi-plus",
                    text="New annotation",
                )
