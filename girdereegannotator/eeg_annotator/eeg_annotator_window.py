from multiprocessing import Pipe, Process
from typing import Any

from .eeg_annotator_worker import worker_main


class EEGAnnotatorError(Exception):
    pass


class EGGAnnotatorWindow:
    def __init__(self) -> None:
        self._events = [
            "MouseMove",
            "LeftButtonPress",
            "RightButtonPress",
            "KeyDown",
        ]

        self._cols = 0
        self._rows = 0
        self.window_size = {"w": 0, "h": 0}

        self._worker_started = False

    def __del__(self) -> None:
        self._stop_worker()

    def _start_worker(self) -> None:
        self._parent_conn, child_conn = Pipe()

        self._process = Process(
            target=worker_main,
            args=(child_conn,),
            daemon=True,
        )

        self._process.start()
        self._worker_started = True

    def _stop_worker(self) -> None:
        if self._process.is_alive():
            self._parent_conn.send(("quit", None))
            self._process.join()
            self._worker_started = False

    def _restart_worker(self) -> None:
        if self._worker_started:
            self._stop_worker()
        self._start_worker()

    def set_file_path(self, file_path: str) -> None:
        self._restart_worker()
        self._parent_conn.send(("open", file_path))
        status = self._parent_conn.recv()

        if status[0] == "error":
            _, msg = status
            raise EEGAnnotatorError(f"Could not load file into annotator: {msg}")

    def _move(self, x: float, y: float) -> None:
        self._parent_conn.send(("move", (x, y)))

    def _click(self, button: str) -> None:
        self._parent_conn.send(("click", button))

    def _keydown(self, key: str) -> None:
        self._parent_conn.send(("keydown", key))

    def _is_point_in_window(self, x: float, y: float) -> bool:
        return 0 <= x <= self._cols and 0 <= y <= self._rows

    @property
    def img_cols_rows(self) -> tuple[Any, int, int]:
        self._parent_conn.send(("frame", None))

        return self._parent_conn.recv()

    def process_resize_event(self, width: int, height: int) -> None:
        self.window_size = {"w": width, "h": height}
        self._parent_conn.send(("resize", (width, height)))

    def process_interaction_event(self, event: Any) -> bool:
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
