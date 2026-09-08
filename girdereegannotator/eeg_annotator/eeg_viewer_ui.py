from dataclasses import dataclass, field

from trame.widgets import html, rca
from trame.widgets import vuetify3 as v3

from girdereegannotator.database.models import Asset
from girdereegannotator.utils.base_ui import BaseUI
from girdereegannotator.utils.load_status import (
    LoadErrorMessage,
    LoadProgress,
    LoadStatus,
)

from .components.rca_view import RCAViewMode


@dataclass
class EEGViewerState:
    load_status: LoadStatus = LoadStatus.UNDEFINED
    status_message: str | None = None
    eeg_asset: Asset = field(default_factory=Asset)
    annotations_asset: Asset = field(default_factory=Asset)
    mode: RCAViewMode = RCAViewMode.UNDEFINED


class EEGViewerUI(html.Div, BaseUI[EEGViewerState]):
    def __init__(self, ref: str = "eegview", **kwargs) -> None:
        super().__init__(classes="viewer", **kwargs)
        self._ref = ref
        self._root_elem_ref = f"trame.refs.{self._ref}.$refs.rootElem"
        self._init_typed_state(self.state, EEGViewerState)

        with self, v3.VFadeTransition(mode="out-in"):
            with html.Div(v_if=self._is_load_status(LoadStatus.LOADING), classes="viewer__load"):
                LoadProgress()

            with html.Div(
                v_else_if=f"{self._is_load_status(LoadStatus.ERROR)} && {self.name.status_message} != null",
            ):
                LoadErrorMessage(status_message=self.name.status_message)

            with (
                html.Div(v_else_if=self._is_load_status(LoadStatus.LOADED), classes="viewer__content"),
                v3.VHover(
                    v_slot="{ props }",
                    update_modelValue=(
                        "(value) => {if ("
                        f"value && {self._root_elem_ref} != window.document.activeElement"
                        ") {"
                        f"{self._root_elem_ref}.focus();"
                        "} }"
                    ),
                ),
            ):
                self.rca = rca.RemoteControlledArea(
                    v_bind="props",
                    ref=self._ref,
                    send_mouse_move=True,
                )

    def _is_load_status(self, load_status: LoadStatus) -> str:
        return f"({self.name.load_status} == {load_status.value})"
