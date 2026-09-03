from dataclasses import dataclass, field
from enum import Enum, auto

from girdereegannotator.database.models import AnnotationsFile, EEGFileset


class EEGAnnotatorMode(Enum):
    UNDEFINED = auto()
    READONLY = auto()
    ANNOTATE = auto()
    REVIEW = auto()
    DONE = auto()


@dataclass
class EEGAnnotatorState:
    eeg_fileset: EEGFileset = field(default_factory=EEGFileset)
    annotations_file: AnnotationsFile = field(default_factory=AnnotationsFile)
    mode: EEGAnnotatorMode = EEGAnnotatorMode.UNDEFINED
