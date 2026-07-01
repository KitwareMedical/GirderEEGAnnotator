from trame.widgets import html, rca
from trame.widgets import vuetify3 as v3

from .eeg_annotator_shortcuts_panel import ShortcutsPanel


class EGGAnnotatorUI(html.Div):
    def __init__(self, **kwargs) -> None:
        super().__init__(classes="fill-height", **kwargs)
        self._ref = "eegview"
        self._root_elem_ref = f"trame.refs.{self._ref}.$refs.rootElem"
        self._build_ui()

    def _build_ui(self) -> None:
        with (
            self,
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
            ShortcutsPanel()
