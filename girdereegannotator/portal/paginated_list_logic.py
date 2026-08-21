import asyncio
from asyncio import Task
from collections.abc import Callable
from typing import Generic, TypeVar

from trame_server import Server
from trame_server.utils.typed_state import TypedState

from girdereegannotator.portal.components.expandable_list import ExpandableListState
from girdereegannotator.utils.base_logic import BaseLogic
from girdereegannotator.utils.load_status import LoadStatus

V = TypeVar("V")


class PaginatedListLogic(BaseLogic[ExpandableListState[V]], Generic[V]):
    def __init__(
        self,
        server: Server,
        list_state: TypedState[ExpandableListState[V]],
        load_callable: Callable[..., list[V]],
        filter_callable: Callable[[V], bool] | None = None,
        count_all_callable: Callable[..., None] | None = None,
        limit: int = 15,
    ):
        super().__init__(server, typed_state=list_state)
        self.load_callable = load_callable
        self.count_all_callable = count_all_callable
        self.limit = limit

        self.filter_callable = filter_callable
        self.database_offset = 0
        self.database_exhausted = False

        # Task tracking for cancellation
        self._append_task: Task | None = None
        self._count_task: Task | None = None

    def _cancel_tasks(self) -> None:
        """Cancel any ongoing fetch or count tasks to prevent race conditions."""
        if self._append_task and not self._append_task.done():
            self._append_task.cancel()
        if self._count_task and not self._count_task.done():
            self._count_task.cancel()

    def _load_paged_items(self, search_text: str | None = None, **kwargs) -> list[V]:
        return self.load_callable(
            offset=len(self.data.items),
            limit=self.limit,
            search_text=search_text,
            **kwargs,
        )

    def _load_filtered_items(self, search_text: str | None = None, **kwargs) -> list[V]:
        result: list[V] = []

        while (not self.limit or len(result) < self.limit) and not self.database_exhausted:
            database_limit = self.limit - len(result)
            item_list = self.load_callable(
                offset=self.database_offset,
                limit=database_limit,
                search_text=search_text,
                **kwargs,
            )

            self.database_offset += len(item_list)
            result.extend(item for item in item_list if self.filter_callable(item))

            if not self.limit or len(item_list) < database_limit:
                self.database_exhausted = True

        return result

    def reset(self) -> None:
        self._cancel_tasks()
        self.data.items = []
        self.data.current_index = None
        self.data.load_status = LoadStatus.UNDEFINED
        self.data.status_message = None
        self.data.max_index = None

        self.database_offset = 0
        self.database_exhausted = False

    def append_list_items(self, search_text: str | None = None, **kwargs) -> Task | None:
        if self.data.load_status == LoadStatus.LOADING:
            return None

        self.data.load_status = LoadStatus.LOADING

        async def _append_list_item_task() -> None:
            try:
                item_list = await asyncio.to_thread(
                    self._load_filtered_items if self.filter_callable else self._load_paged_items,
                    search_text=search_text,
                    **kwargs,
                )
                self.data.load_status = (
                    LoadStatus.LOADED if not self.limit or len(item_list) < self.limit else LoadStatus.UNDEFINED
                )
                self.data.items = self.data.items + item_list

            except asyncio.CancelledError:
                pass
            except Exception as e:
                self.data.load_status = LoadStatus.ERROR
                self.data.status_message = str(e)

        self._append_task = self.create_async_task(_append_list_item_task)
        return self._append_task

    def count_items(self, search_text: str | None = None, **kwargs) -> Task | None:
        if self._count_task and not self._count_task.done():
            self._count_task.cancel()

        async def _count_items_task() -> None:
            try:
                item_list = await asyncio.to_thread(self.load_callable, limit=0, **kwargs)

                if self.count_all_callable is not None:
                    self.count_all_callable(item_list)

                if search_text:
                    item_list = await asyncio.to_thread(self.load_callable, limit=0, search_text=search_text, **kwargs)

                if self.filter_callable is None:
                    self.data.max_index = len(item_list)
                else:
                    self.data.max_index = sum(self.filter_callable(item) for item in item_list)

            except asyncio.CancelledError:
                pass

        self._count_task = self.create_async_task(_count_items_task)
        return self._count_task
