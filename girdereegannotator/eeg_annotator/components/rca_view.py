import shutil
from enum import Enum, auto
from pathlib import Path
from typing import Any

import libeegviz
import numpy as np
from PIL import Image

from girdereegannotator.database.models import Asset


class RCAViewMode(Enum):
    UNDEFINED = auto()
    READONLY = auto()
    EDIT = auto()


class RCAViewError(Exception): ...


class RCAView:
    def __init__(self):
        self._context = None
        self._events = ["MouseMove", "LeftButtonPress", "RightButtonPress", "KeyDown"]
        self._cols, self._rows = 0, 0
        self.window_size = {"w": 0, "h": 0}
        self.tmp_annotations_asset = Asset(name="tmp_annotations_file.tsv")

    def update_viewer_mode(self, mode: RCAViewMode) -> None:
        if mode == RCAViewMode.UNDEFINED:
            self._events = []
        elif mode == RCAViewMode.READONLY:
            self._events = ["MouseMove", "KeyDown"]
        else:
            self._events = ["MouseMove", "LeftButtonPress", "RightButtonPress", "KeyDown"]

    def save_annotations_asset(self, annotations_asset_path: str) -> None:
        if not Path(self.tmp_annotations_asset.path).exists():
            raise FileNotFoundError(f"{self.tmp_annotations_asset.path} does not exist")

        if not Path(annotations_asset_path).exists():
            raise FileNotFoundError(f"{annotations_asset_path} does not exist")

        shutil.copy(self.tmp_annotations_asset.path, annotations_asset_path)

    def set_eeg_file(self, dir_path: str, eeg_file_path: str) -> None:
        if not Path(eeg_file_path).exists():
            raise FileNotFoundError(f"{eeg_file_path} does not exist")

        self.tmp_annotations_asset.path = str(Path(dir_path) / self.tmp_annotations_asset.name)

        try:
            self._context = libeegviz.create2(eeg_file_path, self.tmp_annotations_asset.path)
        except Exception as e:
            raise RCAViewError(f"Could not open {eeg_file_path} in viewer") from e

    def set_annotations_asset(self, annotations_asset_path: str) -> None:
        if self._context is None:
            return

        if not Path(annotations_asset_path).exists():
            raise FileNotFoundError(f"{annotations_asset_path} does not exist")

        try:
            libeegviz.load_annotations(self._context, annotations_asset_path)
        except Exception as e:
            raise RCAViewError(f"Could not open annotations file {annotations_asset_path} in viewer") from e

    def _move(self, x: float, y: float) -> None:
        if self._context is None:
            return
        libeegviz.move(self._context, x, y)

    def _click(self, button: str) -> None:
        if self._context is None:
            return
        libeegviz.click(self._context, button)

    def _keydown(self, key: str) -> None:
        if self._context is None:
            return
        libeegviz.key(self._context, key)

    def _is_point_in_window(self, x: float, y: float) -> None:
        return 0 <= x <= self._cols and 0 <= y <= self._rows

    def rgba_to_rgb(self, rgba_image_array: Any) -> None:
        """Convert an RGBA image array to an RGB image array by alpha blending over a white background."""
        rgba_image_array = rgba_image_array.astype(np.float32) / 255.0
        rgb_array = rgba_image_array[..., :3]
        alpha_array = rgba_image_array[..., 3:]
        bg = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        out_rgb = alpha_array * rgb_array + (1 - alpha_array) * bg  # blending
        return (out_rgb * 255).astype(np.uint8)

    @property
    def img_cols_rows(self) -> tuple[Any, int, int]:
        if self._context is None:
            return (None, 0, 0)
        byte_image, self._cols, self._rows, _ = libeegviz.update(self._context)
        image = Image.frombytes(mode="RGBA", size=(self._cols, self._rows), data=byte_image)
        np_image = np.asarray(image)
        np_image = self.rgba_to_rgb(np_image)
        return (
            np_image,
            self._cols,
            self._rows,
        )

    def process_resize_event(self, width: int, height: int) -> None:
        self.window_size = {"w": width, "h": height}
        if self._context is None:
            return
        libeegviz.resize(self._context, width, height)

    def process_interaction_event(self, event: Any) -> None:
        event_type = event["type"]

        if event_type not in self._events:
            return False

        if not self._is_point_in_window(event.get("x", 0), event.get("y", 0)):
            return False

        if event_type == "MouseMove":
            self._move(int(event["x"]), self._rows - int(event["y"]))
        elif event_type == "LeftButtonPress":
            self._click(0)
        elif event_type == "RightButtonPress":
            self._click(1)
        elif event_type == "KeyDown":
            self._keydown(event.get("key", ""))

        return True
