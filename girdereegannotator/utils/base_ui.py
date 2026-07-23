from typing import Generic, TypeVar

from trame_server.utils.typed_state import State, TypedState

T = TypeVar("T")
V = TypeVar("V")


class BaseUI(Generic[T]):
    def _init_typed_state(self, main_state: State, state_type: type[T] | None) -> None:
        self._state_type = state_type
        self.typed_state: TypedState[T] | None = TypedState(main_state, state_type) if state_type else None

    @property
    def name(self) -> T:
        return self.typed_state.name if self.typed_state else None

    @property
    def data(self) -> T:
        return self.typed_state.data if self.typed_state else None

    def get_sub_state(self, sub_state_name: V) -> TypedState[V] | None:
        if not self.typed_state:
            return None
        return self.typed_state.get_sub_state(sub_state_name)
