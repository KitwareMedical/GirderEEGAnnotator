import logging
from datetime import UTC, datetime
from locale import getlocale
from pathlib import Path
from typing import TypeVar

from girder_client import AuthenticationError as GirderAuthenticationError
from girder_client import GirderClient
from girder_client import HttpError as GirderHTTPError

from ..exceptions import AuthenticationError
from ..interface_database import DatabaseInterface
from ..models import (
    AnnotationFile,
    Asset,
    DatabaseError,
    Dataset,
    EEGFile,
    EEGFileset,
    GirderModel,
    Model,
    User,
)
from .girder_bids_handler import GirderBIDSHandler

T = TypeVar("T", bound=Model)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GirderDatabase(DatabaseInterface):
    """
    Girder-backed implementation of the database interface.

    This backend requires a running Girder instance with the GirderBIDS
    plugin installed and enabled. https://github.com/KitwareMedical/GirderBIDS
    """

    def __init__(self, collection_id: str, api_url: str | None = None, api_key: str | None = None) -> None:
        self.girder_client = GirderClient(apiUrl=api_url)
        self.bids_handler = GirderBIDSHandler(self.girder_client)
        self.authenticated = False
        self.collection_id = collection_id

        if api_key is not None:
            self._api_key_authentication(api_key)

    def _api_key_authentication(self, api_key: str) -> None:
        if not self.authenticated:
            self.girder_client.authenticate(apiKey=api_key)
            self.authenticated = True

    @staticmethod
    def format_date(date_str: str) -> str:
        utc_dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f+00:00")
        utc_dt = utc_dt.replace(tzinfo=UTC)
        local_dt = utc_dt.astimezone()
        loc = getlocale()[0] or ""
        fmt = "%m/%d/%Y %I:%M %p" if loc.startswith("en_US") else "%d/%m/%Y %H:%M"
        return local_dt.strftime(fmt)

    def _clean_doc(self, doc: GirderModel, model: type[T]) -> GirderModel:
        return {k: v for k, v in doc.items() if k in model.fields()}

    def _document_as_dataclass(self, doc: GirderModel, model: type[T]) -> T:
        if doc.get("created"):
            doc["created"] = self.format_date(doc["created"])
        if doc.get("meta"):
            doc["meta"] = {key: str(value) for key, value in doc["meta"].items()}
        return model(**self._clean_doc(doc, model))

    def _user_as_dataclass(self, user: GirderModel) -> User:
        user["first_name"] = user["firstName"]
        user["last_name"] = user["lastName"]
        return self._document_as_dataclass(user, User)

    def logout(self) -> None:
        self.girder_client.delete("user/authentication")
        self.authenticated = False

    def login(self, username: str, password: str) -> User:
        if self.authenticated:
            self.logout()
        try:
            user = self.girder_client.authenticate(username, password)
            self.authenticated = True
        except GirderAuthenticationError as e:
            raise AuthenticationError("Wrong login or password") from e
        except GirderHTTPError as e:
            raise AuthenticationError("Unknown error") from e

        return self._user_as_dataclass(user)

    def get_me(self) -> User | None:
        user = self.girder_client.get(path="user/me")
        return self._user_as_dataclass(user) if user else None

    def list_datasets(self, _collection_id: str | None = None, **kwargs) -> list[Dataset]:
        if not self.authenticated:
            return []
        return self.bids_handler.list_datasets(self.collection_id, **kwargs)

    def list_eeg_filesets(self, dataset: Dataset, **kwargs) -> list[EEGFileset]:
        if not self.authenticated:
            return []
        return self.bids_handler.list_eeg_filesets(dataset, **kwargs)

    def refresh_eeg_fileset(self, eeg_fileset: EEGFileset, compute_eeg: bool = False) -> EEGFileset:
        return self.bids_handler.get_eeg_fileset(eeg_fileset, compute=compute_eeg)

    def _download_file(self, file: EEGFile, download_dir: str, refresh: bool = False) -> Asset:
        file_path = Path(download_dir) / file.name
        return self.bids_handler.download_file(file, file_path, refresh)

    def download_eeg_files(
        self,
        eeg_fileset: EEGFileset,
        download_dir: str,
        annotation_file: AnnotationFile | None = None,
    ) -> tuple[Asset, Asset]:
        if eeg_fileset.eeg._id is None:
            raise DatabaseError(f"No EEG file to load in fileset {eeg_fileset.name}")

        eeg = self._download_file(eeg_fileset.eeg, download_dir)

        if annotation_file is None:
            annotation_name = self.bids_handler.get_next_annotation_file_name(eeg_fileset)
            annotation = Asset(annotation_name, str(Path(download_dir) / annotation_name))
        else:
            # Reload because annotation could have been updated
            annotation = self._download_file(annotation_file, download_dir, refresh=True)

        return eeg, annotation

    def save_annotations(self, eeg_fileset: EEGFileset, annotation: Asset) -> AnnotationFile:
        user = self.get_me()
        return self.bids_handler.upload_annotation(eeg_fileset, annotation, user._id)
