from abc import ABC, abstractmethod
from inspect import getmembers, isfunction

from trame_server.controller import Controller

from .models import AnnotationsFile, Asset, Dataset, EEGFileset, User


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
    def refresh_eeg_fileset(self, eeg_fileset: EEGFileset, compute_eeg: bool = False) -> EEGFileset:
        pass

    @abstractmethod
    def list_datasets(self, collection_id: str | None = None, **kwargs) -> list[Dataset]:
        pass

    @abstractmethod
    def list_eeg_filesets(self, dataset: Dataset, **kwargs) -> list[EEGFileset]:
        pass

    @abstractmethod
    def download_eeg_files(
        self,
        dataset: Dataset,
        eeg_fileset: EEGFileset,
        download_dir: str,
        annotations_file: AnnotationsFile | None = None,
    ) -> tuple[Asset, Asset]:
        pass

    @abstractmethod
    def upload_annotations_file(self, eeg_fileset: EEGFileset, eeg_annotations_asset: Asset) -> AnnotationsFile:
        pass

    @abstractmethod
    def update_annotations_file_status(self, annotations_file: AnnotationsFile) -> None:
        pass

    @abstractmethod
    def delete_annotations_file(self, annotations_file: AnnotationsFile) -> None:
        pass


def register_interface(interface: DatabaseInterface, controller: Controller) -> None:
    """Register all interface methods in the controller"""
    for name, _ in getmembers(DatabaseInterface, predicate=isfunction):
        if hasattr(interface, name):
            controller[name] = getattr(interface, name)
