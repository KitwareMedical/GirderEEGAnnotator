from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import AnnotationsFile, EEGFileset
from girdereegannotator.portal.components.eeg_annotation_list import AnnotationListItem
from girdereegannotator.utils.components import Button, Select


class AnnotationMenu(Select):
    annotation_selected = Signal(AnnotationsFile | None)

    def __init__(
        self,
        annotations_file_state: TypedState[AnnotationsFile],
        eeg_fileset_state: TypedState[EEGFileset],
        eeg_fileset_validated: str,
        **kwargs,
    ) -> None:
        super().__init__(
            v_model=annotations_file_state.name._id,
            density="compact",
            disabled=(f"!{eeg_fileset_state.name.annotations_files}.length",),
            item_title="name",
            item_value="_id",
            items=(eeg_fileset_state.name.annotations_files,),
            placeholder=(f"{eeg_fileset_validated} ? 'Select an annotation' : 'New annotation'",),
            rounded=True,
            **kwargs,
        )
        self.eeg_fileset_state = eeg_fileset_state

        with self:
            with v3.Template(v_slot_item="{ props, item }"):
                AnnotationListItem(
                    v_bind="props",
                    annotation="item.raw",
                    build_actions=False,
                    click=(self._select_annotation, "[item.raw._id]"),
                )

            with v3.Template(v_slot_selection="{ item }"):
                AnnotationListItem(
                    annotation="item.raw",
                    build_actions=False,
                )

    def _select_annotation(self, annotation_id: str) -> None:
        annotation = next(
            (ann for ann in self.eeg_fileset_state.data.annotations_files if ann._id == annotation_id), None
        )
        self.annotation_selected(annotation)


class AnnotationInput(html.Div):
    annotation_selected = Signal(AnnotationsFile | None)

    def __init__(
        self,
        annotations_file_state: TypedState[AnnotationsFile],
        eeg_fileset_state: TypedState[EEGFileset],
        eeg_fileset_validated: str,
        **kwargs,
    ) -> None:
        super().__init__(classes="annotation-input", **kwargs)

        with self:
            Button(
                click=self.annotation_selected,
                color="secondary",
                density="comfortable",
                disabled=(f"!{annotations_file_state.name._id} || {eeg_fileset_validated}",),
                icon="mdi-plus",
                tooltip_location="bottom start",
                tooltip="New annotation",
            )

            v3.VDivider(vertical=True)

            with html.Div(classes="annotation-input__menu"):
                annotation_menu = AnnotationMenu(annotations_file_state, eeg_fileset_state, eeg_fileset_validated)
                annotation_menu.annotation_selected.connect(self.annotation_selected)
