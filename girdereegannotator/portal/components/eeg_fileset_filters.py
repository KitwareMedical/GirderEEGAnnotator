from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from .filters.annotator_filter import AnnotatorFilter, AnnotatorState
from .filters.search_filter import SearchFilter, SearchState
from .filters.status_filter import StatusFilter, StatusState


@dataclass
class EEGFilesetFiltersState:
    search_state: SearchState = field(default_factory=SearchState)
    annotator_state: AnnotatorState = field(default_factory=AnnotatorState)
    status_state: StatusState = field(default_factory=StatusState)


class EEGFilesetFilters(html.Div):
    annotator_updated = Signal()
    search_clicked = Signal()
    status_clicked = Signal()

    def __init__(self, filter_state: TypedState[EEGFilesetFiltersState], **kwargs) -> None:
        super().__init__(classes="list-filters button-bar", **kwargs)

        with self:
            StatusFilter(
                status_state=filter_state.get_sub_state(filter_state.name.status_state),
                on_status_clicked=self.status_clicked,
            )
            v3.VSpacer()
            AnnotatorFilter(
                annotator_state=filter_state.get_sub_state(filter_state.name.annotator_state),
                on_annotator_updated=self.annotator_updated,
            )
            SearchFilter(
                search_state=filter_state.get_sub_state(filter_state.name.search_state),
                on_search_clicked=self.search_clicked,
            )
