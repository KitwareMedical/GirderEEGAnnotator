from pathlib import Path
from typing import Any
from yaml import safe_load

from .interface_database import DatabaseInterface
from .girder_database import GirderDatabase


def load_config(path: str) -> Any:
    with Path(path).open() as f:
        return safe_load(f)


def get_interface(config: dict[str, Any]) -> DatabaseInterface:
    backend = config.get("backend")

    if backend is None:
        raise ValueError("The configuration file must define a backend.")

    ptype = backend.get("type")
    if ptype == "girder":
        return GirderDatabase(api_url=backend.get("api_url"), api_key=backend.get("api_key"))

    raise ValueError("The backend type is undefined or unknown.")
