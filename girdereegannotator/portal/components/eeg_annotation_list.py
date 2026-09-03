from typing import Any

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import AnnotationStatus, EEGFileset, User
from girdereegannotator.utils.components import Button


class AnnotationListItemElement(html.Div):
    def __init__(self, annotation: str, **kwargs):
        super().__init__(**kwargs)
        self.user_state = TypedState(self.state, User)
        self.annotation = annotation

    def _is_annotation_status(self, annotation_status: AnnotationStatus) -> str:
        return f"({self.annotation}.status === {annotation_status.value})"

    def _is_annotation_author(self) -> str:
        return f"({self.annotation}.author._id === {self.user_state.name._id})"


class AnnotationListItemStatusTag(AnnotationListItemElement):
    def __init__(self, annotation: str, **kwargs):
        super().__init__(annotation, classes="px-2", **kwargs)
        with self:
            v3.VIcon(
                icon="mdi-tag",
                color=(
                    f"{self._is_annotation_status(AnnotationStatus.IN_PROGRESS)} ? 'warning' : "
                    f"({self._is_annotation_status(AnnotationStatus.IN_REVIEW)} ? 'info' : 'success')",
                ),
            )


class AnnotationListItemAuthorTag(AnnotationListItemElement):
    def __init__(self, annotation: str, **kwargs):
        super().__init__(annotation, classes="px-2", **kwargs)
        with self:
            html.Div(
                f"{{{{ {annotation}.author.login }}}}",
                classes=(
                    f"{self._is_annotation_author()} ? 'text-caption font-weight-medium text-secondary' : 'font-weight-medium text-caption'",
                ),
            )


class AnnotationListItemMenu(AnnotationListItemElement):
    delete_clicked = Signal(dict[str, Any])

    def __init__(self, annotation: str, **kwargs):
        super().__init__(annotation, **kwargs)
        with self, v3.VMenu(location="start"):
            with v3.Template(v_slot_activator="{ props }"):
                Button(
                    v_bind="props",
                    icon="mdi-dots-vertical",
                )
            with v3.VCard():
                Button(
                    prepend_icon="mdi-delete",
                    color="error",
                    click=(self.delete_clicked, f"[{self.annotation}]"),
                    disabled=(
                        f"!{self._is_annotation_author()} || {self._is_annotation_status(AnnotationStatus.DONE)}",
                    ),
                    text="Delete",
                    rounded=False,
                    variant="text",
                )


class AnnotationListItem(v3.VListItem):
    annotation_selected = Signal(str)
    delete_clicked = Signal(dict[str, Any])

    def __init__(self, annotation: str, build_actions: bool = True, **kwargs) -> None:
        super().__init__(classes="annotation-list-item", title=(f"{annotation}.name",), **kwargs)
        with self:
            if build_actions:
                with v3.Template(v_slot_append=True):
                    actions = AnnotationListItemMenu(annotation)
                    self._connect_menu(actions)

            with v3.Template(v_slot_prepend=True):
                AnnotationListItemStatusTag(annotation)

            with v3.Template(v_slot_subtitle=True):
                AnnotationListItemAuthorTag(annotation)

    def _connect_menu(self, menu: AnnotationListItemMenu) -> None:
        menu.delete_clicked.connect(self.delete_clicked)


class AnnotationList(v3.VList):
    new_annotation_clicked = Signal()
    annotation_selected = Signal(str | None)
    delete_clicked = Signal(str)

    def __init__(self, eeg_fileset_state: TypedState[EEGFileset], **kwargs) -> None:
        super().__init__(classes="annotation-list", **kwargs)
        self.eeg_fileset_state = eeg_fileset_state

        with self:
            self.delete_dialog = AnnotationDeleteDialog(namespace="portal", on_delete=self.delete_clicked)

            with html.Div(v_for=f"(annotation, annotation_index) in {eeg_fileset_state.name.annotations_files}"):
                list_item = AnnotationListItem(
                    "annotation",
                    click=(self.annotation_selected, "[annotation._id]"),
                )
                self._connect_list_item(list_item)

                v3.VDivider(
                    v_if=f"annotation_index + 1 < {eeg_fileset_state.name.annotations_files}.length", classes="mx-4"
                )

            with html.Div(classes="d-flex justify-center"):
                Button(
                    click=self.new_annotation_clicked,
                    variant="flat",
                    color="primary",
                    prepend_icon="mdi-plus",
                    text="New annotation",
                )

    def _connect_list_item(self, list_item: AnnotationListItem) -> None:
        list_item.annotation_selected.connect(self.annotation_selected)
        list_item.delete_clicked.connect(self.delete_dialog.set_annotation_to_delete)


class AnnotationDeleteDialog(v3.VDialog):
    def __init__(self, namespace: str, on_delete: Signal, **kwargs):
        model = f"{namespace}_annotation_delete_dialog"
        super().__init__(v_model=(model, False), width=800, **kwargs)
        self._model = model
        self._annotation_to_delete = f"{namespace}_annotation_to_delete"
        self._on_delete = on_delete

        with (
            self,
            v3.VCard(
                v_if=model,
                title=(f"`Delete ${{ {self._annotation_to_delete}.name }}`",),
                text="Are you sure to delete this annotations file ?",
            ),
            v3.VCardActions(),
        ):
            Button(
                click=self._cancel,
                text="Cancel",
                variant="tonal",
            )
            Button(
                click=(self._delete, f"[{self._annotation_to_delete}._id]"),
                color="error",
                text="Delete",
                variant="flat",
            )

    def _cancel(self) -> None:
        self.state[self._model] = False
        self.state[self._model] = None

    def set_annotation_to_delete(self, annotation: dict[str, Any]) -> None:
        self.state[self._model] = True
        self.state[self._annotation_to_delete] = annotation

    def _delete(self, annotation_id: str) -> None:
        self._on_delete(annotation_id)
        self._cancel()
