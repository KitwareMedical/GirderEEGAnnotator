from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import Model
from girdereegannotator.utils.components import Button
from girdereegannotator.utils.load_status import (
    LoadErrorMessage,
    LoadProgress,
    LoadStatus,
)

V = TypeVar("V", bound=Model)


LoadCallback = Callable[[], Any]


@dataclass
class ExpandableListState(Generic[V]):
    items: list[V] = field(default_factory=list)
    filtered_out_ids: list[str] = field(default_factory=list)
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
            html.Span("{{ value }}", classes="text-right text-body-2 text-ellipsis")


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
    item_expanded = Signal(V)

    def __init__(self, item_state: TypedState[V], list_state: TypedState[T], **kwargs) -> None:
        super().__init__(
            classes="expandable-list",
            **kwargs,
        )

        self.item_state = item_state
        self.list_state = list_state
        self.item = "item"

        with self, v3.VFadeTransition(mode="out-in"):
            with html.Div(v_if=self.is_load_status(LoadStatus.LOADING), classes="expandable-list__load"):
                LoadProgress()

            with html.Div(
                v_if=f"{self.is_load_status(LoadStatus.ERROR)} && {self.list_state.name.status_message} != null",
                classes="expandable-list__error",
            ):
                LoadErrorMessage(status_message=self.list_state.name.status_message)

            with html.Div(
                v_else=True,
                classes="expandable-list__content",
            ):
                with (
                    v3.VVirtualScroll(classes="expandable-list__content-list", items=(list_state.name.items,)),
                    v3.Template(v_slot_default=f"{{ {self.item} }}"),
                    html.Div(
                        v_if=f"!{list_state.name.filtered_out_ids}.includes({self.item}._id)",
                    ),
                ):
                    with (
                        ExpandableListItem(
                            expanded=f"{item_state.name._id} === {self.item}._id",
                            click=(self.expand_item, f"[{self.item}._id]"),
                            title=(f"{self.item}.name",),
                        ),
                        v3.Template(v_slot_append=True),
                    ):
                        self.action_slot = html.Div(classes="button-bar")

                    with (
                        v3.VExpandTransition(),
                        html.Div(v_if=f"{item_state.name._id} === {self.item}._id"),
                    ):
                        self.expand_slot = v3.VCard(classes="expansion-card", flat=True, border=True)

                self.count_slot = html.Div(
                    classes="expandable-list__content-count",
                )

    def is_load_status(self, load_status: LoadStatus) -> str:
        return f"({self.list_state.name.load_status} == {load_status.value})"

    def build_select_item_button(self, **kwargs) -> None:
        Button(
            color=kwargs.pop("color", "primary"),
            flat=kwargs.pop("flat", True),
            click_stop=(self.select_item, f"[{self.item}._id]"),
            **kwargs,
        )

    def build_metadata(self, metadata: str) -> None:
        ExpandableListItemMetadata(metadata)

    def build_count(self, item_type: str) -> None:
        with v3.VFadeTransition(mode="out-in"):
            html.Span(
                f"No {item_type}",
                v_if=f"{self._number_of_items} === 0",
            )
            html.Span(
                f"{{{{ {self._number_of_items} }}}} {item_type}",
                v_else=True,
                key=(f"{self.list_state.name.items}.length",),
            )

    def select_item(self, item_id: str) -> None:
        item = next(it for it in self.list_state.data.items if it._id == item_id)
        self.item_selected(item)

    def expand_item(self, item_id: str) -> V | None:
        if self.item_state.data._id == item_id:
            item = None
        else:
            item = next(it for it in self.list_state.data.items if it._id == item_id)

        self.item_expanded(item)

    @property
    def _number_of_items(self) -> str:
        return f"{self.list_state.name.items}.length - {self.list_state.name.filtered_out_ids}.length"
