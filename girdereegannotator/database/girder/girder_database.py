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
    AnnotationsFile,
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


def handle_database_error(e: GirderHTTPError) -> DatabaseError:
    if e.status == 401:
        msg = "Unauthorized"
    elif e.status == 403:
        msg = "Access denied"
    else:
        msg = "Invalid request"
    return DatabaseError(msg)


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
        user["name"] = " ".join([str(user["firstName"]).capitalize(), str(user["lastName"]).upper()])
        user["short_name"] = str(user["firstName"])[0].upper() + str(user["lastName"])[0].upper()
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
            raise AuthenticationError(f"Authentication error: {handle_database_error(e)}") from e

        return self._user_as_dataclass(user)

    def get_me(self) -> User | None:
        try:
            user = self.girder_client.get(path="user/me")
            return self._user_as_dataclass(user) if user else None
        except GirderHTTPError as e:
            raise DatabaseError(f"Could not fetch current user: {handle_database_error(e)}") from e

    def list_datasets(self, _collection_id: str | None = None, **kwargs) -> list[Dataset]:
        if not self.authenticated:
            return []
        try:
            return self.bids_handler.list_datasets(self.collection_id, **kwargs)
        except GirderHTTPError as e:
            raise DatabaseError(f"Could not list datasets: {handle_database_error(e)}") from e

    def list_eeg_filesets(self, dataset: Dataset, **kwargs) -> list[EEGFileset]:
        if not self.authenticated:
            return []
        try:
            return self.bids_handler.list_eeg_filesets(dataset, **kwargs)
        except GirderHTTPError as e:
            if e.status == 403:
                msg = "Access denied"
            elif e.status == 401:
                msg = "Unauthorized"
            else:
                msg = "Invalid request"
            raise DatabaseError(f"Could not list EEGs: {msg}") from e

    def refresh_eeg_fileset(self, eeg_fileset: EEGFileset, compute_eeg: bool = False) -> EEGFileset:
        try:
            return self.bids_handler.get_eeg_fileset(eeg_fileset, compute=compute_eeg)
        except GirderHTTPError as e:
            raise DatabaseError(f"Could not refresg EEG {eeg_fileset.name}: {handle_database_error(e)}") from e

    def _download_file(self, file: EEGFile, download_dir: str, refresh: bool = False) -> Asset:
        try:
            file_path = Path(download_dir) / file.name
            return self.bids_handler.download_file(file, file_path, refresh)
        except GirderHTTPError as e:
            raise DatabaseError(f"Could not download file {file.name}: {handle_database_error(e)}") from e

    def download_eeg_files(
        self,
        eeg_fileset: EEGFileset,
        download_dir: str,
        annotations_file: AnnotationsFile | None = None,
    ) -> tuple[Asset, Asset]:
        if eeg_fileset.eeg._id is None:
            raise DatabaseError(f"No EEG file to load in fileset {eeg_fileset.name}")

        eeg_asset = self._download_file(eeg_fileset.eeg, download_dir)

        if annotations_file is None:
            annotations_asset_name = self.bids_handler.get_next_annotations_file_name(eeg_fileset)
            annotations_asset_path = Path(download_dir) / annotations_asset_name
            if annotations_asset_path.exists():
                annotations_asset_path.unlink()
            annotations_asset_path.touch()
            annotations_asset = Asset(annotations_asset_name, str(annotations_asset_path))

        else:
            # Reload because annotation could have been updated
            annotations_asset = self._download_file(annotations_file, download_dir, refresh=True)

        return eeg_asset, annotations_asset

    def upload_annotations_file(self, eeg_fileset: EEGFileset, annotations_asset: Asset) -> AnnotationsFile:
        try:
            user = self.get_me()
            return self.bids_handler.upload_annotations_file(eeg_fileset, annotations_asset, user)
        except GirderHTTPError as e:
            raise DatabaseError(
                f"Could not upload annotations file {annotations_asset.name} to {eeg_fileset.name}: {handle_database_error(e)}"
            ) from e

    def update_annotations_file_status(self, annotations_file: AnnotationsFile) -> None:
        try:
            self.bids_handler.update_annotation_status(annotations_file)
        except GirderHTTPError as e:
            raise DatabaseError(
                f"Could not update annotations file ({annotations_file.name}) status to {annotations_file.status.value}: {handle_database_error(e)}"
            ) from e

    def delete_annotations_file(self, annotations_file: AnnotationsFile) -> None:
        try:
            self.girder_client.delete(f"item/{annotations_file._id}")
        except GirderHTTPError as e:
            raise DatabaseError(
                f"Could not delete annotations file ({annotations_file.name}): {handle_database_error(e)}"
            ) from e
