from typing import Any

from trame.widgets.html import Span
from trame.widgets.vuetify3 import VAvatar, VBtn, VIcon, VTooltip


class Button(VBtn):
    def __init__(
        self,
        avatar_text: str | None = None,
        text_transform: str | tuple[Any] | None = None,
        tooltip: str | tuple[Any] | None = None,
        tooltip_location: str = "right",
        **kwargs,
    ) -> None:
        icon = kwargs.pop("icon", None)
        text = kwargs.pop("text", None)
        color = kwargs.pop("color", None)

        if avatar_text is not None:
            kwargs["icon"] = True
            kwargs["size"] = kwargs.get("size", "large")
            kwargs["variant"] = kwargs.get("variant", "text")
        elif icon:
            kwargs["icon"] = True
            kwargs["variant"] = kwargs.get("variant", "text")
        else:
            kwargs["rounded"] = True
            kwargs["color"] = color

        text_transform = "uppercase" if kwargs.get("block", False) else text_transform or "none"
        kwargs["style"] = " ".join([kwargs.get("style", ""), f"text-transform: {text_transform};"])
        kwargs["__events"] = [*kwargs.get("__events", []), ("click_stop", "click.stop")]

        super().__init__(**kwargs)

        with self:
            if text and not isinstance(text, bool):
                Span(text)
            if icon and not isinstance(icon, bool):
                VIcon(icon=icon, color=color)
            if avatar_text:
                with VAvatar(color=color):
                    Span(avatar_text)
            if tooltip:
                VTooltip(
                    activator="parent",
                    close_delay=100,
                    location=tooltip_location,
                    open_delay=500,
                    text=tooltip,
                )
