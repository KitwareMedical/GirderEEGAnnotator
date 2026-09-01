from dataclasses import dataclass
from enum import Enum

from trame_server.utils.typed_state import TypedState

from girdereegannotator.utils.components import Select


class AnnotationAuthor(Enum):
    UNDEFINED = "Any"
    ME = "Me"
    NOT_ME = "Not me"


@dataclass
class AnnotationAuthorState:
    author: AnnotationAuthor = AnnotationAuthor.UNDEFINED


class AnnotationAuthorFilter(Select):
    def __init__(self, author_state: TypedState[AnnotationAuthorState], **kwargs):
        super().__init__(
            v_model=author_state.name.author,
            items=(str([annotator.value for annotator in AnnotationAuthor]),),
            label="Annotation author",
            **kwargs,
        )
