import re
from dataclasses import dataclass
from threading import Lock

from ..models import EEGFileset, FileExtension, FileSuffix


@dataclass
class BIDSDerivativeContext:
    derivatives_dataset_id: str | None = None
    derivatives_folder_id: str | None = None


class BIDSNamingStrategy:
    """Handles string manipulations, suffix removals, and BIDS annotation naming rules."""

    def __init__(self) -> None:
        self.suffix = FileSuffix()
        self.ext = FileExtension()

    def extract_base_name(self, filename: str) -> str:
        return filename.removesuffix(self.ext.eeg).removesuffix(self.suffix.eeg)

    def generate_filtered_eeg_name(self, original_filename: str) -> str:
        base_name = self.extract_base_name(original_filename)
        return f"{base_name}_desc-filtered{self.suffix.eeg}{self.ext.eeg}"

    def get_next_annotations_file_name(self, eeg_fileset: EEGFileset) -> str:
        """Return the annotation filename using the smallest available number."""
        pattern = re.compile(r"_desc-annotation(\d+)_")

        used_numbers = {
            int(match.group(1))
            for annotation in eeg_fileset.annotations_files
            if (match := pattern.search(annotation.name))
        }

        next_number = 1
        while next_number in used_numbers:
            next_number += 1

        base_name = self.extract_base_name(eeg_fileset.name)
        annotations_desc = f"desc-annotation{next_number}"
        return f"{base_name}_{annotations_desc}{self.suffix.annotation}{self.ext.annotation}"


class BIDSContextManager:
    def __init__(self):
        self._dataset_map: dict[str, BIDSDerivativeContext] = {}
        self._fileset_map: dict[str, BIDSDerivativeContext] = {}
        self._lock = Lock()

    def set_dataset(self, dataset_id: str, ctx: BIDSDerivativeContext) -> None:
        with self._lock:
            self._dataset_map[dataset_id] = ctx

    def get_dataset(self, dataset_id: str | None) -> BIDSDerivativeContext:
        if not dataset_id:
            raise ValueError("Dataset ID cannot be None.")
        with self._lock:
            if dataset_id not in self._dataset_map:
                raise KeyError(f"No BIDS derivative context found for Dataset ID '{dataset_id}'.")
            return self._dataset_map[dataset_id]

    def set_fileset(self, fileset_id: str, ctx: BIDSDerivativeContext) -> None:
        with self._lock:
            self._fileset_map[fileset_id] = ctx

    def get_fileset(self, fileset_id: str) -> BIDSDerivativeContext:
        with self._lock:
            if fileset_id not in self._fileset_map:
                raise KeyError(f"No BIDS derivative context found for EEGFileset ID '{fileset_id}'.")
            return self._fileset_map[fileset_id]
