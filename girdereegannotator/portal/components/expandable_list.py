from dataclasses import dataclass, field
from typing import Generic, TypeVar

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

V = TypeVar("V")


@dataclass
class ExpandableListState(Generic[V]):
    current_index: int | None = None
    items: list[V] = field(default_factory=list)


T = TypeVar("T", bound=ExpandableListState)


class ExpandableListItem(v3.VListItem):
    def __init__(self, expanded: str, **kwargs):
        super().__init__(
            classes=("['portal-list-item', { 'portal-list-item--expanded': " + expanded + " }]",),
            active=(expanded,),
            rounded=True,
            **kwargs,
        )
        with self, v3.Template(v_slot_prepend="{ isActive }"):
            v3.VIcon(
                icon="mdi-chevron-down",
                style=("{ transform: isActive ? 'rotate(180deg)' : 'rotate(0deg)'}",),
            )


class ExpandableList(v3.VList, Generic[T, V]):
    item_selected = Signal(V)

    def __init__(self, list_state: TypedState[T], **kwargs) -> None:
        super().__init__(
            classes="portal-list",
            variant="tonal",
            **kwargs,
        )
        self.list_state = list_state
        self.item = "item"
        self.index = "index"

        with self, html.Div(v_for=f"({self.item}, {self.index}) in {list_state.name.items}"):
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

    def build_select_item_button(self, **kwargs) -> None:
        v3.VBtn(
            color=kwargs.pop("color", "primary"),
            variant=kwargs.pop("variant", "plain"),
            click_stop=(self.select_item, f"[{self.index}]"),
            __events=[("click_stop", "click.stop")],
            **kwargs,
        )

    def select_item(self, index: int) -> None:
        self.list_state.data.current_index = index
        self.item_selected(self.list_state.data.items[index])
