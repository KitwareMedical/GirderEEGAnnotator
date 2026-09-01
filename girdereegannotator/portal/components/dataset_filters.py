from trame.widgets import html
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from .filters.search_filter import SearchFilter, SearchState


class DatasetFilters(html.Div):
    filter_changed = Signal()

    def __init__(self, filter_state: TypedState[SearchState], **kwargs) -> None:
        super().__init__(classes="list-filters", **kwargs)

        with self:
            search_filter = SearchFilter(search_state=filter_state)
            search_filter.search_clicked.connect(self.filter_changed)
