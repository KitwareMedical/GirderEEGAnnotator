from datetime import datetime, timezone
from locale import getlocale
from pathlib import Path
from typing import TypeVar

from attr import dataclass
from girder_client import GirderClient

from .interface_database import DatabaseInterface
from .models import Collection, EEGMedia, EEGMediaFile, GirderModel, Model, User

T = TypeVar("T", bound=Model)


@dataclass
class GirderResources:
    collection: str = "collection"
    user: str = "user"
    media: str = "item"
    file: str = "file"


class GirderDatabase(DatabaseInterface):
    def __init__(self, api_url: str | None = None, api_key: str | None = None) -> None:
        self.girder_client = GirderClient(apiUrl=api_url)
        self.resources = GirderResources()
        self.authenticated = False

        if api_key is not None:
            self._api_key_authentication(api_key)

    def _api_key_authentication(self, api_key: str) -> None:
        if not self.authenticated:
            self.girder_client.authenticate(apiKey=api_key)
            self.authenticated = True

    @staticmethod
    def format_date(date_str: str) -> str:
        utc_dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f+00:00")
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        local_dt = utc_dt.astimezone()
        loc = getlocale()[0] or ""
        fmt = "%m/%d/%Y %I:%M %p" if loc.startswith("en_US") else "%d/%m/%Y %H:%M"
        return local_dt.strftime(fmt)

    def _clean_doc(self, doc: GirderModel, model: type[T]) -> GirderModel:
        return {k: v for k, v in doc.items() if k in model.fields()}

    def _document_as_dataclass(self, doc: GirderModel, model: type[T]) -> T:
        if doc.get("created"):
            doc["created"] = self.format_date(doc["created"])
        return model(**self._clean_doc(doc, model))

    def _user_as_dataclass(self, user: GirderModel) -> User:
        user["first_name"] = user["firstName"]
        user["last_name"] = user["lastName"]
        return self._document_as_dataclass(user, User)

    def logout(self) -> None:
        self.girder_client.delete(f"{self.resources.user}/authentication")
        self.authenticated = False

    def list_collections(
        self,
        search_mode: str | None = None,
        search_query: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str = "created",
        sort_dir: int = -1,
    ) -> list[Collection]:
        params = {"sort": sort, "sortdir": sort_dir}
        if search_query:
            params.update({"searchQuery": search_query})
        if search_mode:
            params.update({"searchMode": search_mode})
        collections = self.girder_client.listResource(
            path=self.resources.collection,
            params=params,
            limit=limit,
            offset=offset,
        )
        return [self._document_as_dataclass(collection, Collection) for collection in collections]

    def list_eeg_media(
        self,
        sort: str = "created",
        sort_dir: int = -1,
    ) -> list[EEGMedia]:
        params = {"text": "*.edf", "sort": sort, "sortdir": sort_dir, "offset": 0, "limit": None}
        media_items = self.girder_client.get(
            path=self.resources.media,
            parameters=params,
        )
        return [self._document_as_dataclass(media, EEGMedia) for media in media_items]


    def download_eeg_media_files(self, media_id: str, download_dir: str) -> list[EEGMediaFile]:
        girder_media_files = self.girder_client.listResource(path=f"{self.resources.media}/{media_id}/files")
        media_files = []

        for media_file in girder_media_files:
            image_request = self.girder_client.get(
                f"{self.resources.file}/{media_file['_id']}/download", jsonResp=False
            )
            media_file_path = Path(download_dir) / media_file["name"]
            with media_file_path.open("wb") as f:
                f.write(image_request.content)

            media_files.append(EEGMediaFile(name=media_file["name"], path=str(media_file_path)))

        return media_files

    def save_eeg_annotations(self, eeg_media_id: str, eeg_annotation_file: EEGMediaFile):
        pass