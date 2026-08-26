from trame.widgets import html
from trame.widgets import vuetify3 as v3
from undo_stack import Signal

from girdereegannotator.database.models import AnnotationStatus
from girdereegannotator.utils.components import Button


class AnnotationList(v3.VList):
    def __init__(self, user_id: str, fileset_id: str, annotations: str, select_callable: Signal, **kwargs) -> None:
        super().__init__(**kwargs)

        with self:
            with html.Div(v_for=f"(annotation, annotation_index) in {annotations}"):
                with v3.VListItem(
                    classes="annotation-list-item",
                    title=("annotation.name",),
                ):
                    v3.VIcon(v_if=f"{user_id} === annotation.annotator_id", icon="mdi-account-check")
                    with v3.Template(v_slot_append=True):
                        actions = AnnotationActions(user_id, fileset_id, "annotation")
                        actions.edit_clicked.connect(select_callable)

                    with v3.Template(v_slot_prepend=True):
                        v3.VIcon(
                            v_if=self._is_annotation_status(AnnotationStatus.IN_PROGRESS),
                            icon="mdi-tag",
                            color="warning",
                        )
                        v3.VIcon(
                            v_else_if=self._is_annotation_status(AnnotationStatus.IN_REVIEW),
                            icon="mdi-tag",
                            color="info",
                        )
                        v3.VIcon(
                            v_else_if=self._is_annotation_status(AnnotationStatus.DONE), icon="mdi-tag", color="success"
                        )

                v3.VDivider(v_if=f"annotation_index + 1 < {annotations}.length", classes="mx-4")

            with html.Div(classes="d-flex justify-center"):
                Button(
                    click=(select_callable, f"[{fileset_id}]"),
                    variant="flat",
                    color="primary",
                    prepend_icon="mdi-plus",
                    text="New annotation",
                )

    def _is_annotation_status(self, annotation_status: AnnotationStatus) -> str:
        return f"(annotation.status === {annotation_status.value})"


class AnnotationActions(html.Div):
    view_clicked = Signal(str)
    edit_clicked = Signal(str)
    duplicate_clicked = Signal(str)
    delete_clicked = Signal(str)

    def __init__(
        self,
        user_id: str,
        fileset_id: str,
        annotation: str,
        **kwargs,
    ):
        super().__init__(classes="button-bar", **kwargs)

        with self:
            self._build_button(
                icon="mdi-eye",
                color="secondary",
                click=(self.view_clicked, f"[{fileset_id}, {annotation}._id]"),
                tooltip="View annotation",
            )
            self._build_button(
                icon="mdi-pencil",
                color="secondary",
                click=(self.edit_clicked, f"[{fileset_id}, {annotation}._id]"),
                disabled=(f"{user_id} !== {annotation}.annotator_id",),
                tooltip="Edit annotation",
            )
            self._build_button(
                icon="mdi-content-copy",
                click=(self.duplicate_clicked, f"[{annotation}._id]"),
                tooltip="Duplicate annotation",
            )
            self._build_button(
                icon="mdi-close-circle-outline",
                color="error",
                click=(self.delete_clicked, f"[{annotation}._id]"),
                disabled=(f"{user_id} !== {annotation}.annotator_id",),
                tooltip="Delete annotation",
            )

    def _build_button(self, **kwargs) -> None:
        Button(tooltip_location="top", tooltip_open_delay=800, **kwargs)
