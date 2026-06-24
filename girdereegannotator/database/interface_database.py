from abc import ABC, abstractmethod
from inspect import getmembers, isfunction

from trame_server.controller import Controller

from .models import Collection, EEGMedia, EEGMediaFile


class DatabaseInterface(ABC):
    @abstractmethod
    def login(self, username: str, password: str) -> None:
        pass

    @abstractmethod
    def logout(self) -> None:
        pass

    @abstractmethod
    def list_collections(self, limit: int, offset: int, sort: str, sort_dir: int) -> list[Collection]:
        pass

    @abstractmethod
    def list_eeg_media(self, limit: int, offset: int, sort: str, sort_dir: int) -> list[EEGMedia]:
        pass

    @abstractmethod
    def download_eeg_media_files(self, media_id: str, download_dir: str) -> list[EEGMediaFile]:
        pass

    @abstractmethod
    def save_eeg_annotations(self, eeg_media_id: str, eeg_annotation_file: EEGMediaFile) -> EEGMedia:
        pass


def register_interface(interface: DatabaseInterface, controller: Controller) -> None:
    """Register all interface methods in the controller"""
    for name, _ in getmembers(DatabaseInterface, predicate=isfunction):
        if hasattr(interface, name):
            controller[name] = getattr(interface, name)
