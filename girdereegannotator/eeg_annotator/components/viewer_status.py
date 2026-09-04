from trame.widgets import html
from trame.widgets import vuetify3 as v3


class ViewerStatus(html.Div):
    def __init__(self, is_readonly: str, **kwargs):
        super().__init__(classes="viewer-status", **kwargs)

        with self:
            v3.VTooltip("Read only", v_if=is_readonly, activator="parent")
            v3.VIcon(v_if=is_readonly, icon="mdi-lock")
