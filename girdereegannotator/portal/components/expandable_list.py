from dataclasses import dataclass, field
from typing import Generic, TypeVar

from trame.widgets import html
from trame.widgets import vuetify3 as v3
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.utils.components import Button

V = TypeVar("V")


@dataclass
class ExpandableListState(Generic[V]):
    current_index: int | None = None
    items: list[V] = field(default_factory=list)
    can_load_more_items: bool = True


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


class ExpandableList(v3.VList, Generic[T, V]):
    item_selected = Signal(V)
    load_more_items = Signal()

    def __init__(self, ref: str, list_state: TypedState[T], **kwargs) -> None:
        super().__init__(
            classes="expandable-list",
            **kwargs,
        )
        self.scroll_ref = ref
        self.list_state = list_state
        self.item = "item"
        self.index = "index"

        with (
            self,
            v3.VInfiniteScroll(
                ref=self.scroll_ref,
                empty_text="",
                height="100%",
                load=f"trigger('{self.server.trigger_name(self._load_more)}')"
                ".then((result) => { console.log('Load more result:', result); $event.done(result ? 'ok' : 'empty'); });",
            ),
        ):
            with v3.Template(v_slot_loading=True):
                self.load_slot = html.Div()

            with html.Div(
                v_for=f"({self.item}, {self.index}) in {list_state.name.items}",
                key=f"{self.item}.name",
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

    async def _load_more(self) -> bool:
        if self.list_state.data.can_load_more_items:
            self.load_more_items()
        return self.list_state.data.can_load_more_items

    def reset_scroll(self) -> None:
        self.server.js_call(self.scroll_ref, "reset")

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
