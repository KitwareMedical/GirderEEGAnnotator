from typing import Any

from .girder import GirderDatabase
from .interface_database import DatabaseInterface


def get_interface(config: dict[str, Any]) -> DatabaseInterface:
    backend = config.get("backend")

    if backend is None:
        raise ValueError("The configuration file must define a backend.")

    ptype = backend.get("type")
    if ptype == "girder":
        return GirderDatabase(
            collection_id=backend.get("collection_id"),
            api_url=backend.get("api_url"),
            api_key=backend.get("api_key"),
        )

    raise ValueError("The backend type is undefined or unknown.")
