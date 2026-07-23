from collections.abc import Callable
from typing import Any, Generic, TypeVar

from trame_server import Server
from trame_server.state import State
from trame_server.utils.typed_state import TypedState

T = TypeVar("T")
V = TypeVar("V")


class BaseLogic(Generic[T]):
    def __init__(self, server: Server, state_type: type[T] | None):
        self._server = server
        self._state_type = state_type
        self.typed_state: TypedState[T] | None = TypedState(self.state, state_type) if state_type else None

    @property
    def server(self) -> Server:
        return self._server

    @property
    def state(self) -> State:
        return self._server.state

    @property
    def ctrl(self) -> State:
        return self._server.controller

    @property
    def name(self) -> T:
        return self.typed_state.name if self.typed_state else None

    @property
    def data(self) -> T:
        return self.typed_state.data if self.typed_state else None

    def bind_changes(self, change_dict: dict[Any | list[Any] | tuple[Any], Callable]) -> None:
        if self.typed_state:
            self.typed_state.bind_changes(change_dict)

    def get_sub_state(self, sub_state_name: V) -> TypedState[V] | None:
        if self.typed_state is None:
            return None
        return self.typed_state.get_sub_state(sub_state_name)

    def set_ui(self, ui: Any) -> None:
        pass

    def reset_state(self) -> None:
        if self.typed_state and self._state_type:
            self.typed_state.set_dataclass(self._state_type())
