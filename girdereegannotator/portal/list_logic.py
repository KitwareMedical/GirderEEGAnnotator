import asyncio
from asyncio import Task
from collections.abc import Callable
from typing import Generic, TypeVar

from trame_server import Server
from trame_server.utils.typed_state import TypedState

from girdereegannotator.database.models import Model
from girdereegannotator.portal.components.expandable_list import ExpandableListState
from girdereegannotator.utils.base_logic import BaseLogic
from girdereegannotator.utils.load_status import LoadStatus

V = TypeVar("V", bound=Model)


class ListLogic(BaseLogic[ExpandableListState[V]], Generic[V]):
    def __init__(
        self,
        server: Server,
        list_state: TypedState[ExpandableListState[V]],
        on_load: Callable[..., list[V]],
        on_filter: Callable[[V], bool] | None = None,
        on_count: Callable[..., None] | None = None,
    ):
        super().__init__(server, typed_state=list_state)
        self.load = on_load
        self.count = on_count
        self.filter = on_filter
        self._fetch_task: Task | None = None

    def _cancel_task(self) -> None:
        if self._fetch_task and not self._fetch_task.done():
            self._fetch_task.cancel()

    def _fetch_items(self, **kwargs) -> list[V]:
        item_list = self.load(offset=0, limit=0, **kwargs)

        if self.count is not None:
            self.count(item_list)

        return item_list

    def _filter_items(self, search_text: str | None = None) -> list[str]:
        excluded_ids = set()
        if search_text:
            excluded_ids.update(item._id for item in self.data.items if search_text not in item.name)

        if self.filter is not None:
            excluded_ids.update(item._id for item in self.data.items if not self.filter(item))

        return list(excluded_ids)

    def reset(self) -> None:
        self._cancel_task()
        self.data.items = []
        self.data.load_status = LoadStatus.UNDEFINED
        self.data.status_message = None

    def fetch_item_list(self, search_text: str | None = None, **kwargs) -> Task | None:
        if self.data.load_status == LoadStatus.LOADING:
            return None

        self.data.load_status = LoadStatus.LOADING

        async def _fetch_item_list_task() -> None:
            try:
                self.data.items = await asyncio.to_thread(self._fetch_items, **kwargs)
                self.data.excluded_ids = self._filter_items(search_text=search_text)
                self.data.load_status = LoadStatus.LOADED

            except asyncio.CancelledError:
                pass
            except Exception as e:
                self.data.load_status = LoadStatus.ERROR
                self.data.status_message = str(e)

        self._fetch_task = self.create_async_task(_fetch_item_list_task)
        return self._fetch_task

    def update_item(self, updated_item: V) -> None:
        self.data.items = [updated_item if updated_item._id == item._id else item for item in self.data.items]

    def exclude_item(self, item_to_exclude: V) -> None:
        if item_to_exclude._id not in self.data.excluded_ids:
            self.data.excluded_ids = [*self.data.excluded_ids, item_to_exclude._id]

    def include_item(self, item_to_include: V) -> None:
        if item_to_include._id in self.data.excluded_ids:
            self.data.excluded_ids = [item_id for item_id in self.data.excluded_ids if item_id != item_to_include._id]
