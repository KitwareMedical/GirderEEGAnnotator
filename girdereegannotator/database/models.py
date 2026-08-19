from dataclasses import asdict, dataclass, field, fields
from typing import Any

GirderModel = dict[str, Any]
GirderParams = dict[str, Any]


@dataclass
class BIDSSuffix:
    eeg: str = "_eeg"
    annotation: str = "_events"


@dataclass
class BIDSExtension:
    eeg: str = ".edf"
    annotation: str = ".tsv"


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
class BIDSDataset(Model):
    _id: str | None = None
    name: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    derivative_dataset_id: str | None = None


@dataclass
class EEGFile(Model):
    _id: str | None = None
    name: str | None = None


@dataclass
class AnnotationFile(EEGFile):
    annotator_id: str | None = None


@dataclass
class EEGFileset:
    name: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    raw_eeg: EEGFile = field(default_factory=EEGFile)
    eeg: EEGFile = field(default_factory=EEGFile)
    annotations: list[AnnotationFile] = field(default_factory=list)
    upload_dataset_id: str | None = None
    upload_folder_id: str | None = None


@dataclass
class Asset:
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
