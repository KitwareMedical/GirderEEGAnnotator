from trame.widgets import html
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from .filters.search_filter import SearchFilter, SearchState


class DatasetFilters(html.Div):
    search_clicked = Signal()

    def __init__(self, filter_state: TypedState[SearchState], **kwargs) -> None:
        super().__init__(classes="list-filters", **kwargs)

        with self:
            SearchFilter(search_state=filter_state, on_search_clicked=self.search_clicked)
