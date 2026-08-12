from abc import ABC, abstractmethod
from inspect import getmembers, isfunction

from trame_server.controller import Controller

from .models import AnnotationFile, Asset, BIDSDataset, EEGMedia, User


class DatabaseInterface(ABC):
    @abstractmethod
    def login(self, username: str, password: str) -> User:
        pass

    @abstractmethod
    def logout(self) -> None:
        pass

    @abstractmethod
    def get_me(self) -> User | None:
        pass

    @abstractmethod
    def list_datasets(self, collection_id: str | None = None) -> list[BIDSDataset]:
        pass

    @abstractmethod
    def list_eeg_media(self, dataset: BIDSDataset, limit: int, offset: int, sort: str, sort_dir: int) -> list[EEGMedia]:
        pass

    @abstractmethod
    def download_eeg_media_files(
        self,
        dataset: BIDSDataset,
        eeg_media: EEGMedia,
        download_dir: str,
        annotation_file: AnnotationFile | None = None,
    ) -> tuple[Asset, Asset]:
        pass

    @abstractmethod
    def save_annotations(self, eeg_media: EEGMedia, eeg_annotation_file: AnnotationFile) -> AnnotationFile:
        pass


def register_interface(interface: DatabaseInterface, controller: Controller) -> None:
    """Register all interface methods in the controller"""
    for name, _ in getmembers(DatabaseInterface, predicate=isfunction):
        if hasattr(interface, name):
            controller[name] = getattr(interface, name)
