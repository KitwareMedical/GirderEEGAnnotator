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


class AnnotationListItemActions(AnnotationListItemElement):
    view_clicked = Signal(str)
    delete_clicked = Signal(str)

    def __init__(self, annotation: str, **kwargs):
        super().__init__(annotation, classes="button-bar", **kwargs)
        with self:
            self._build_action_button(
                icon="mdi-eye",
                color="secondary",
                click=(self.view_clicked, f"[{self.annotation}._id]"),
                tooltip="View annotation",
            )
            self._build_action_button(
                icon="mdi-close-circle-outline",
                color="error",
                click=(self.delete_clicked, f"[{self.annotation}._id]"),
                disabled=(f"!{self._is_annotation_author()} || {self._is_annotation_status(AnnotationStatus.DONE)}",),
                tooltip="Delete annotation",
            )

    def _build_action_button(self, **kwargs) -> None:
        Button(tooltip_location="top", tooltip_open_delay=800, density="compact", **kwargs)


class AnnotationListItem(v3.VListItem):
    view_clicked = Signal(str)
    delete_clicked = Signal(str)

    def __init__(self, annotation: str, build_actions: bool, **kwargs) -> None:
        super().__init__(classes="annotation-list-item", title=(f"{annotation}.name",), subtitle="aaaaa", **kwargs)
        with self:
            if build_actions:
                with v3.Template(v_slot_append=True):
                    actions = AnnotationListItemActions(annotation)
                    self._connect_actions(actions)

            with v3.Template(v_slot_prepend=True):
                AnnotationListItemStatusTag(annotation)

            with v3.Template(v_slot_subtitle=True):
                AnnotationListItemAuthorTag(annotation)

    def _connect_actions(self, actions: AnnotationListItemActions) -> None:
        actions.view_clicked.connect(self.view_clicked)
        actions.delete_clicked.connect(self.delete_clicked)


class AnnotationList(v3.VList):
    new_clicked = Signal()
    view_clicked = Signal(int | None)
    delete_clicked = Signal(int)

    def __init__(self, eeg_fileset_state: TypedState[EEGFileset], build_actions: bool = True, **kwargs) -> None:
        super().__init__(classes="annotation-list", **kwargs)
        self.eeg_fileset_state = eeg_fileset_state

        with self:
            with html.Div(v_for=f"(annotation, annotation_index) in {eeg_fileset_state.name.annotations_files}"):
                list_item = AnnotationListItem("annotation", build_actions)
                self._connect_list_item(list_item)

                v3.VDivider(
                    v_if=f"annotation_index + 1 < {eeg_fileset_state.name.annotations_files}.length", classes="mx-4"
                )

            if build_actions:
                with html.Div(classes="d-flex justify-center"):
                    Button(
                        click=self.new_clicked,
                        variant="flat",
                        color="primary",
                        prepend_icon="mdi-plus",
                        text="New annotation",
                    )

    def _connect_list_item(self, list_item: AnnotationListItem) -> None:
        list_item.view_clicked.connect(self.view_clicked)
        list_item.delete_clicked.connect(self.delete_clicked)
