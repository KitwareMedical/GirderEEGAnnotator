from trame_server.core import Server

from girdereegannotator.core import AnnotatorApp
from girdereegannotator.database.database_config import load_config, get_interface


def main(server: Server | None = None, **kwargs) -> None:
    config = load_config(path="config.yaml")
    interface = get_interface(config)
    app = AnnotatorApp(interface=interface, server=server)
    app.server.start(**kwargs)


if __name__ == "__main__":
    main()
