from dataclasses import asdict, dataclass, field, fields
from typing import Any

GirderModel = dict[str, Any]


@dataclass
class Model:
    @classmethod
    def fields(cls) -> list[str]:
        return [f.name for f in fields(cls)]

    def as_dict(self, extra_fields: dict[str, Any] | None = None) -> dict[str, Any]:
        model_dict = asdict(self)

        if isinstance(extra_fields, dict):
            model_dict.update(extra_fields)

        return model_dict


@dataclass
class Collection(Model):
    _id: str
    name: str
    meta: dict[str, Any]


@dataclass
class EEGMediaMetadata(Model):
    annotation_id: str | None = None


@dataclass
class EEGMedia(Model):
    _id: str | None = None
    name: str | None = None
    meta: EEGMediaMetadata = field(default_factory=EEGMediaMetadata)


@dataclass
class EEGMediaFile(Model):
    name: str | None = None
    path: str | None = None


@dataclass
class User(Model):
    _id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    login: str | None = None
    email: str | None = None

    def as_params(self) -> dict[str, Any]:
        return {"firstName": self.first_name, "lastName": self.last_name, "email": self.email}
