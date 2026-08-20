from trame.widgets import html
from trame_server.utils.typed_state import TypedState

from .search_filter import Search, SearchState


class EEGFilesetFilters(html.Div):
    def __init__(self, filter_state: TypedState[SearchState], **kwargs) -> None:
        super().__init__(classes="list-filters button-bar", **kwargs)

        with self:
            self.search = Search(search_state=filter_state)
