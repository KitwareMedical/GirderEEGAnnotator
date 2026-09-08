from dataclasses import dataclass
from enum import Enum, auto

from trame.widgets import vuetify3 as v3
from trame.widgets.html import Div
from trame_server.utils.typed_state import TypedState


class NavigationWindow(Enum):
    UNDEFINED = auto()
    PORTAL = auto()
    ANNOTATOR = auto()


@dataclass
class NavigationState:
    window: NavigationWindow = NavigationWindow.UNDEFINED


class NavigationCard(v3.VCard):
    def __init__(self, nav_state: TypedState[NavigationState], **kwargs):
        super().__init__(
            v_if=f"!{self._is_navigation_window(nav_state, NavigationWindow.UNDEFINED)}",
            classes="fill-height",
            flat=True,
            rounded="lg",
            **kwargs,
        )

        with self:
            with v3.VCardItem(classes="nav-bar"):
                self.portal_breadcrumbs = Div(classes="portal-breadcrumbs")
                self.annotator_toolbar = Div(
                    v_if=self._is_navigation_window(nav_state, NavigationWindow.ANNOTATOR),
                    classes="annotator-toolbar",
                )
                self.portal_toolbar = Div(
                    v_else_if=self._is_navigation_window(nav_state, NavigationWindow.PORTAL),
                    classes="portal-toolbar",
                )

            with (
                v3.VCardText(classes="nav-content"),
                v3.VWindow(v_model=(nav_state.name.window,), classes="nav-window-group"),
            ):
                self.portal = v3.VWindowItem(classes="nav-window", value=(NavigationWindow.PORTAL.value,))
                self.annotator = v3.VWindowItem(
                    classes="nav-window annotator-window", value=(NavigationWindow.ANNOTATOR.value,)
                )

    def _is_navigation_window(self, nav_state: TypedState[NavigationState], nav_window: NavigationWindow) -> str:
        return f"({nav_state.name.window} === {nav_window.value})"
