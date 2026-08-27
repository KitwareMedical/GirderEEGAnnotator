from abc import ABC, abstractmethod
from inspect import getmembers, isfunction

from trame_server.controller import Controller

from .models import AnnotationFile, Asset, Dataset, EEGFileset, User


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
    def refresh_eeg_fileset(self, eeg_fileset: EEGFileset) -> EEGFileset:
        pass

    @abstractmethod
    def download_eeg_files(
        self,
        dataset: Dataset,
        eeg_fileset: EEGFileset,
        download_dir: str,
        annotation_file: AnnotationFile | None = None,
    ) -> tuple[Asset, Asset]:
        pass

    @abstractmethod
    def save_annotations(self, eeg_fileset: EEGFileset, eeg_annotation_file: AnnotationFile) -> AnnotationFile:
        pass


def register_interface(interface: DatabaseInterface, controller: Controller) -> None:
    """Register all interface methods in the controller"""
    for name, _ in getmembers(DatabaseInterface, predicate=isfunction):
        if hasattr(interface, name):
            controller[name] = getattr(interface, name)
