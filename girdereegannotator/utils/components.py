from typing import Any

from trame.widgets.html import Span
from trame.widgets.vuetify3 import VAvatar, VBtn, VIcon, VSelect, VTooltip


class Button(VBtn):
    def __init__(
        self,
        avatar_text: str | None = None,
        text_transform: str | tuple[Any] | None = None,
        tooltip: str | tuple[Any] | None = None,
        tooltip_location: str = "right",
        tooltip_open_delay: int = 500,
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
            kwargs["flat"] = kwargs.get("flat", True)

        text_transform = "uppercase" if kwargs.get("block", False) else text_transform or "none"
        kwargs["style"] = " ".join([kwargs.get("style", ""), f"text-transform: {text_transform};"])
        kwargs["__events"] = [*kwargs.get("__events", []), ("click_stop", "click.stop")]
        kwargs["__properties"] = [*kwargs.get("__properties", []), "type"]

        super().__init__(**kwargs)

        with self:
            if text and not isinstance(text, bool):
                Span(text)
            if icon and not isinstance(icon, bool):
                VIcon(icon=icon, color=color)
            if avatar_text:
                with VAvatar():
                    Span(avatar_text, style=f"color: rgb(var(--v-theme-{color}));")
            if tooltip:
                VTooltip(
                    activator="parent",
                    close_delay=100,
                    location=tooltip_location,
                    open_delay=tooltip_open_delay,
                    text=tooltip,
                )


class Select(VSelect):
    def __init__(self, **kwargs):
        super().__init__(
            bg_color=kwargs.pop("bg_color", "surface-variant"),
            color=kwargs.pop("color", "secondary"),
            density=kwargs.pop("density", "comfortable"),
            flat=kwargs.pop("flat", True),
            hide_details=kwargs.pop("hide_details", True),
            icon_color=kwargs.pop("icon_color", "secondary"),
            variant=kwargs.pop("variant", "solo"),
            **kwargs,
        )
