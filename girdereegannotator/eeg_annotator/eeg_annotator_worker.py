from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any

import libeegviz
import numpy as np
from PIL import Image


class EEGAnnotatorWorker:
    def __init__(self):
        self._context = None
        self._cols = 0
        self._rows = 0

    def set_file_path(self, file_path: str) -> None:
        if not Path(file_path).exists():
            raise FileNotFoundError(file_path)

        self._context = libeegviz.create(file_path)

    def move(self, x: float, y: float) -> None:
        if self._context is not None:
            libeegviz.move(self._context, x, y)

    def click(self, button: int) -> None:
        if self._context is not None:
            libeegviz.click(self._context, button)

    def keydown(self, key: str) -> None:
        if self._context is not None:
            libeegviz.key(self._context, key)

    def resize(self, width: int, height: int) -> None:
        if self._context is not None:
            libeegviz.resize(self._context, width, height)

    @staticmethod
    def rgba_to_rgb(rgba_image_array: Any) -> np.array:
        rgba_image_array = rgba_image_array.astype(np.float32) / 255.0
        rgb = rgba_image_array[..., :3]
        alpha = rgba_image_array[..., 3:]
        bg = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        out = alpha * rgb + (1 - alpha) * bg
        return (out * 255).astype(np.uint8)

    def frame(self) -> tuple[Any, int, int]:
        if self._context is None:
            return None, 0, 0

        byte_image, self._cols, self._rows, _ = libeegviz.update(self._context)
        rgba_image = np.asarray(Image.frombytes("RGBA", (self._cols, self._rows), byte_image))
        rgb_image = self.rgba_to_rgb(rgba_image)

        return rgb_image, self._cols, self._rows


def worker_main(conn: Connection) -> None:
    annotator = EEGAnnotatorWorker()
    while True:
        cmd, payload = conn.recv()
        if cmd == "quit":
            break

        if cmd == "open":
            try:
                annotator.set_file_path(payload)
            except Exception as e:
                conn.send(("error", str(e)))
            else:
                conn.send(("ok",))
        elif cmd == "resize":
            annotator.resize(*payload)
        elif cmd == "move":
            annotator.move(*payload)
        elif cmd == "click":
            annotator.click(payload)
        elif cmd == "keydown":
            annotator.keydown(payload)
        elif cmd == "frame":
            conn.send(annotator.frame())

    conn.close()
