from dataclasses import dataclass
from enum import Enum

from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal


class Annotator(Enum):
    UNDEFINED = "Any"
    ME = "Me"
    NOT_ME = "Not me"


@dataclass
class AnnotatorState:
    annotator: Annotator = Annotator.UNDEFINED


class AnnotatorFilter(v3.VSelect):
    def __init__(self, annotator_state: TypedState[AnnotatorState], on_annotator_updated: Signal, **kwargs):
        super().__init__(
            v_model=annotator_state.name.annotator,
            label="Annotator",
            variant="solo",
            flat=True,
            bg_color="surface-variant",
            items=(str([annotator.value for annotator in Annotator]),),
            update_modelValue=on_annotator_updated,
            density="comfortable",
            color="secondary",
            icon_color="secondary",
            **kwargs,
        )
