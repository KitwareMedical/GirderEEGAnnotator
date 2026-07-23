from trame.app import TrameApp
from trame_server.core import Server

from .app import AnnotatorAppLogic, AnnotatorAppUI
from .database.interface_database import (
    DatabaseInterface,
    register_interface,
)


class AnnotatorApp(TrameApp):
    def __init__(self, server: Server, interface: DatabaseInterface):
        super().__init__(server)
        self.register_interface(interface)

        self._logic = AnnotatorAppLogic(self.server)
        self._ui = AnnotatorAppUI(self.server)

        self.set_ui()

    def set_ui(self) -> None:
        self._logic.set_ui(self._ui)

    def register_interface(self, interface: DatabaseInterface) -> None:
        """Link all database APIs to controller"""
        if interface is not None:
            register_interface(interface, self.ctrl)
