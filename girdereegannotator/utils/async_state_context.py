from asyncio import Task
from collections.abc import Callable
from inspect import iscoroutinefunction

from trame_server import Server
from trame_server.utils.asynchronous import create_task


class AsyncStateContext:
    def __init__(
        self,
        server: Server,
    ) -> None:
        self.server = server.root_server
        self.state = server.state

    async def __aenter__(self) -> None:
        self.state.flush()
        await self.server.network_completion

    async def __aexit__(self, *_args) -> None:
        self.state.flush()
        await self.server.network_completion


def create_async_task(
    tracker: AsyncStateContext,
    callable_method: Callable[..., None],
    *args,
) -> Task:
    async def async_task() -> None:
        async with tracker:
            if iscoroutinefunction(callable_method):
                await callable_method(*args)
            else:
                callable_method(*args)

    return create_task(async_task())
