from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.utils.components import Button
from girdereegannotator.utils.load_status import (
    LoadErrorMessage,
    LoadProgress,
    LoadStatus,
)

V = TypeVar("V")


LoadCallback = Callable[[], Any]


@dataclass
class ExpandableListState(Generic[V]):
    current_index: int | None = None
    items: list[V] = field(default_factory=list)
    load_status: LoadStatus = LoadStatus.UNDEFINED
    status_message: str | None = None


T = TypeVar("T", bound=ExpandableListState)


class ExpandableListItemMetadata(v3.VList):
    def __init__(self, metadata: str, **kwargs):
        super().__init__(classes="metadata-list", density="compact", **kwargs)

        with (
            self,
            v3.VListItem(v_for=f"(value, key) in {metadata}", classes="metadata-item"),
            html.Div(classes="metadata-content"),
        ):
            html.Span("{{ key }}", classes="text-subtitle-2")
            html.Span("{{ value }}", classes="text-right text-body-2 metadata-ellipsis")


class ExpandableListItem(v3.VListItem):
    def __init__(self, expanded: str, **kwargs):
        super().__init__(
            classes=("['expandable-list-item', { 'expandable-list-item--expanded': " + expanded + " }]",),
            active=(expanded,),
            rounded=True,
            **kwargs,
        )
        with self, v3.Template(v_slot_prepend="{ isActive }"):
            v3.VIcon(
                icon="mdi-chevron-down",
                style=("{ transform: isActive ? 'rotate(180deg)' : 'rotate(0deg)'}",),
            )


class ExpandableList(html.Div, Generic[T, V]):
    item_selected = Signal(V)

    def __init__(self, list_state: TypedState[T], item_type: str, **kwargs) -> None:
        super().__init__(
            classes="expandable-list",
            **kwargs,
        )
        self.list_state = list_state
        self.item = "item"
        self.index = "index"
        self.load_callback: LoadCallback | None = None

        with self:
            with html.Div(classes="expandable-list__load"):
                LoadProgress(v_if=self.is_load_status(LoadStatus.LOADING))

            with v3.VFadeTransition(mode="out-in"):
                with html.Div(
                    v_if=f"{self.is_load_status(LoadStatus.ERROR)} && {self.list_state.name.status_message} != null",
                    classes="expandable-list__error",
                ):
                    LoadErrorMessage(status_message=self.list_state.name.status_message)

                with html.Div(
                    v_else_if=f"{self.list_state.name.items}.length",
                    classes="expandable-list__content",
                ):
                    with (
                        v3.VList(classes="expandable-list__content-list"),
                        html.Div(
                            v_for=f"({self.item}, {self.index}) in {list_state.name.items}",
                            key=f"{self.item}.name",
                        ),
                    ):
                        with (
                            ExpandableListItem(
                                expanded=f"{list_state.name.current_index} === {self.index}",
                                click=f"{list_state.name.current_index} === {self.index} ? {list_state.name.current_index} = null : {list_state.name.current_index} = {self.index}",
                                title=(f"{self.item}.name",),
                            ),
                            v3.Template(v_slot_append=True),
                        ):
                            self.action_slot = html.Div(classes="button-bar")

                        with (
                            v3.VExpandTransition(),
                            html.Div(v_if=f"{list_state.name.current_index} === {self.index}"),
                        ):
                            self.expand_slot = v3.VCard(classes="expansion-card", flat=True, border=True)

                    with html.Div(classes="expandable-list__content-more"):
                        Button(
                            v_if=self.is_load_status(LoadStatus.UNDEFINED),
                            classes="ma-4",
                            click=self._load_next,
                            color="primary",
                            density="compact",
                            text="Load more",
                            variant="tonal",
                        )

                    with html.Div(classes="expandable-list__content-count"):
                        html.Span(
                            f"{{{{ {list_state.name.items}.length }}}} {item_type} loaded",
                            v_if=self.is_load_status(LoadStatus.UNDEFINED),
                        )
                        html.Span(
                            f"{{{{ {list_state.name.items}.length }}}} {item_type}",
                            v_else_if=self.is_load_status(LoadStatus.LOADED),
                        )

    def is_load_status(self, load_status: LoadStatus) -> str:
        return f"({self.list_state.name.load_status} == {load_status.value})"

    def set_load_callback(self, callback: LoadCallback) -> None:
        self.load_callback = callback

    def _load_next(self) -> None:
        if self.load_callback is None or self.list_state.data.load_status != LoadStatus.UNDEFINED:
            return

        self.load_callback()

    def build_select_item_button(self, **kwargs) -> None:
        Button(
            color=kwargs.pop("color", "primary"),
            flat=kwargs.pop("flat", True),
            click_stop=(self.select_item, f"[{self.index}]"),
            **kwargs,
        )

    def build_metadata(self, metadata: str) -> None:
        ExpandableListItemMetadata(metadata)

    def select_item(self, index: int) -> None:
        self.list_state.data.current_index = index
        self.item_selected(self.list_state.data.items[index])
