from pathlib import Path
from typing import Any

from yaml import safe_load


def load_config(path: str) -> Any:
    with Path(path).open() as f:
        return safe_load(f)
