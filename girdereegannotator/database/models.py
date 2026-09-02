from dataclasses import asdict, dataclass, field, fields
from enum import Enum, auto
from typing import Any

VALIDATION_THRESHOLD = 3

GirderModel = dict[str, Any]
GirderParams = dict[str, Any]


class DatabaseError(Exception): ...


@dataclass
class FileSuffix:
    eeg: str = "_eeg"
    annotation: str = "_events"


@dataclass
class FileExtension:
    eeg: str = ".edf"
    annotation: str = ".tsv"


@dataclass
class Model:
    _id: str | None = None
    name: str | None = None

    @classmethod
    def fields(cls) -> list[str]:
        return [f.name for f in fields(cls)]

    def as_dict(self, extra_fields: dict[str, Any] | None = None) -> dict[str, Any]:
        model_dict = asdict(self)

        if isinstance(extra_fields, dict):
            model_dict.update(extra_fields)

        return model_dict


@dataclass
class User(Model):
    short_name: str | None = None
    login: str | None = None


@dataclass
class Dataset(Model):
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class EEGFile(Model): ...


class AnnotationStatus(Enum):
    IN_PROGRESS = auto()
    IN_REVIEW = auto()
    DONE = auto()


@dataclass
class AnnotationsFile(EEGFile):
    author: User = field(default_factory=User)
    status: AnnotationStatus = AnnotationStatus.IN_PROGRESS


@dataclass(frozen=True)
class EEGFilesetIdentifier:
    _id: str
    name: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EEGFileset(Model):
    metadata: dict[str, str] = field(default_factory=dict)
    eeg: EEGFile = field(default_factory=EEGFile)
    annotations_files: list[AnnotationsFile] = field(default_factory=list)

    @property
    def is_validated(self) -> bool:
        return sum(ann.status == AnnotationStatus.DONE for ann in self.annotations_files) >= VALIDATION_THRESHOLD


@dataclass
class Asset:
    name: str | None = None
    path: str | None = None
