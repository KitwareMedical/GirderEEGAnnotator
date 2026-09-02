from dataclasses import dataclass, field

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from .filters.annotation_author_filter import (
    AnnotationAuthorFilter,
    AnnotationAuthorState,
)
from .filters.search_filter import SearchFilter, SearchState
from .filters.status_filter import StatusFilter, StatusState


@dataclass
class EEGFilesetFiltersState:
    search_state: SearchState = field(default_factory=SearchState)
    author_state: AnnotationAuthorState = field(default_factory=AnnotationAuthorState)
    status_state: StatusState = field(default_factory=StatusState)


class EEGFilesetFilters(html.Div):
    filter_changed = Signal()

    def __init__(self, filter_state: TypedState[EEGFilesetFiltersState], **kwargs) -> None:
        super().__init__(classes="list-filters button-bar", **kwargs)

        filter_state.bind_changes(
            {
                (
                    filter_state.name.status_state.status,
                    filter_state.name.author_state.author,
                ): self._on_filters_changed
            }
        )

        with self:
            StatusFilter(
                status_state=filter_state.get_sub_state(filter_state.name.status_state),
            )
            v3.VSpacer()
            AnnotationAuthorFilter(
                author_state=filter_state.get_sub_state(filter_state.name.author_state),
            )
            search_filter = SearchFilter(
                search_state=filter_state.get_sub_state(filter_state.name.search_state),
            )
            search_filter.search_clicked.connect(self.filter_changed)

    def _on_filters_changed(self, *_args) -> None:
        self.filter_changed()
