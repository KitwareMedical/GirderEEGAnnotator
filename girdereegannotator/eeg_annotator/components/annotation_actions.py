from typing import Any

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from undo_stack import Signal

from girdereegannotator.utils.components import Button


class AnnotationActions(html.Div):
    def __init__(self, **kwargs) -> None:
        super().__init__(classes="annotation-actions", **kwargs)

        with self:
            v3.VDivider(vertical=True)

    def _build_button(self, **kwargs) -> None:
        Button(
            density="comfortable",
            tooltip_location="bottom start",
            **kwargs,
        )


class AnnotateActions(AnnotationActions):
    annotation_saved = Signal()
    annotation_submitted = Signal()
    annotation_deleted = Signal(dict[str, Any])

    def __init__(self, annotation_name: str, annotation_id: str, **kwargs):
        super().__init__(**kwargs)

        with self:
            self._build_button(
                click=self.annotation_saved,
                icon="mdi-content-save-outline",
                tooltip="Save annotations",
            )
            self._build_button(
                click=self.annotation_submitted,
                color="info",
                icon="mdi-send",
                tooltip="Submit for review",
            )
            self._build_button(
                click=(self.annotation_deleted, f"[{{ name: {annotation_name}, _id: {annotation_id} }}]"),
                color="error",
                disabled=(f"!{annotation_id}",),
                icon="mdi-delete",
                tooltip="Delete annotations file",
            )


class ReviewActions(AnnotationActions):
    annotation_approved = Signal()
    annotation_rejected = Signal()
    annotation_unsubmitted = Signal()

    def __init__(self, is_author: str, **kwargs):
        super().__init__(**kwargs)

        with self:
            self._build_button(
                v_if=f"!{is_author}",
                click=self.annotation_approved,
                color="success",
                icon="mdi-check",
                tooltip="Approve annotations",
            )
            self._build_button(
                v_if=f"!{is_author}",
                click=self.annotation_rejected,
                color="error",
                icon="mdi-close",
                tooltip="Reject annotation",
            )
            self._build_button(
                v_else=True,
                click=self.annotation_unsubmitted,
                icon="mdi-undo",
                tooltip="Unsubmit annotation",
            )
