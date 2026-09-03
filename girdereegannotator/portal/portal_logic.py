from asyncio import Task, to_thread

from trame_server import Server
from trame_server.utils.typed_state import TypedState
from undo_stack import Signal

from girdereegannotator.database.models import (
    AnnotationsFile,
    AnnotationStatus,
    Dataset,
    EEGFileset,
    User,
)
from girdereegannotator.utils.base_logic import BaseLogic

from .components.breadcrumbs import BreadcrumbsElement
from .components.filters.annotation_author_filter import AnnotationAuthor
from .components.filters.status_filter import Status
from .list_logic import ListLogic
from .portal_ui import PortalState, PortalUI


class PortalLogic(BaseLogic[PortalState]):
    eeg_fileset_selected = Signal(EEGFileset, AnnotationsFile | None)
    eeg_fileset_unselected = Signal()

    def __init__(self, server: Server) -> None:
        super().__init__(server, PortalState)
        self._dataset_state = self.get_sub_state(self.name.current_dataset)
        self._eeg_fileset_state = self.get_sub_state(self.name.current_eeg_fileset)
        self._user_state = TypedState(self.state, User)

        self.dataset_list_logic = ListLogic[Dataset](
            server,
            self.get_sub_state(self.name.dataset_list_state),
            on_load=self.ctrl.list_datasets,
        )

        self.eeg_fileset_list_logic = ListLogic[EEGFileset](
            server,
            self.get_sub_state(self.name.eeg_fileset_list_state),
            on_load=self.ctrl.list_eeg_filesets,
            on_filter=self._matches_eeg_fileset_filter,
        )

        self.eeg_fileset_list_logic.bind_changes(
            {
                (
                    self.eeg_fileset_list_logic.name.items,
                    self.eeg_fileset_list_logic.name.filtered_out_ids,
                ): self._count_eeg_filesets_per_status
            }
        )
        self.bind_changes(
            {
                self.name.current_breadcrumbs_element: self._on_breadcrumbs_navigated,
            }
        )

    @property
    def dataset(self) -> Dataset:
        return self._dataset_state.get_dataclass()

    @dataset.setter
    def dataset(self, value: Dataset) -> None:
        self._dataset_state.set_dataclass(value)

    @property
    def eeg_fileset(self) -> EEGFileset:
        return self._eeg_fileset_state.get_dataclass()

    @eeg_fileset.setter
    def eeg_fileset(self, value: EEGFileset) -> None:
        self._eeg_fileset_state.set_dataclass(value)

    @property
    def current_eeg_fileset_index(self) -> int:
        return next(
            (i for i, item in enumerate(self.eeg_fileset_list_logic.data.items) if item._id == self.eeg_fileset._id),
            0,
        )

    def _count_eeg_filesets_per_status(self, eeg_fileset_list: list[EEGFileset], *_args) -> None:
        self.data.eeg_fileset_filter_state.status_state.counts = {
            status: sum(
                self._matches_eeg_fileset_filter(f, status, AnnotationAuthor.UNDEFINED) for f in eeg_fileset_list
            )
            for status in Status
        }

    def _matches_eeg_fileset_filter(
        self, eeg_fileset: EEGFileset, status: Status | None = None, author: AnnotationAuthor | None = None
    ) -> bool:
        status = status or self.data.eeg_fileset_filter_state.status_state.status
        author = author or self.data.eeg_fileset_filter_state.author_state.author

        if status == Status.DONE and not eeg_fileset.is_validated:
            return False
        if status not in [Status.DONE, Status.UNDEFINED] and eeg_fileset.is_validated:
            return False

        annotations_files = eeg_fileset.annotations_files
        if status == Status.TO_DO:
            return not any(annotations_files)

        if author == AnnotationAuthor.ME:
            annotations_files = [ann for ann in annotations_files if ann.author._id == self._user_state.data._id]
        elif author == AnnotationAuthor.NOT_ME:
            annotations_files = [ann for ann in annotations_files if ann.author._id != self._user_state.data._id]

        if status == Status.IN_REVIEW:
            return any(ann.status == AnnotationStatus.IN_REVIEW for ann in annotations_files)

        if status == Status.IN_PROGRESS:
            return any(ann.status == AnnotationStatus.IN_PROGRESS for ann in annotations_files)

        if status == Status.DONE:
            return any(ann.status == AnnotationStatus.DONE for ann in annotations_files)

        # Status.UNDEFINED
        return True

    def fetch_datasets(self) -> Task | None:
        return self.dataset_list_logic.fetch_item_list(search_text=self.data.dataset_filter_state.search_text)

    def fetch_eeg_filesets(self) -> Task | None:
        self.data.eeg_fileset_filter_state.status_state.counts = {}

        if self.dataset._id is None:
            self.data.eeg_fileset_filter_state.status_state.status = Status.UNDEFINED
            self.data.eeg_fileset_filter_state.author_state.author = AnnotationAuthor.UNDEFINED
            self.eeg_fileset_list_logic.reset()
            return None

        return self.eeg_fileset_list_logic.fetch_item_list(
            dataset=self.dataset,
            search_text=self.data.eeg_fileset_filter_state.search_state.search_text,
        )

    def filter_datasets(self) -> Task | None:
        return self.dataset_list_logic.filter_item_list(search_text=self.data.dataset_filter_state.search_text)

    def filter_eeg_filesets(self) -> Task | None:
        return self.eeg_fileset_list_logic.filter_item_list(
            search_text=self.data.eeg_fileset_filter_state.search_state.search_text
        )

    def refresh(self) -> None:
        """Reloads the active view from scratch."""
        if self.dataset._id is None:
            self.dataset = Dataset()
            self.fetch_datasets()
        else:
            self.eeg_fileset = EEGFileset()
            self.fetch_eeg_filesets()

    def _on_dataset_selected(self, dataset: Dataset) -> None:
        self.dataset = dataset
        self.data.current_breadcrumbs_element = BreadcrumbsElement.DATASET
        self.fetch_eeg_filesets()

    def _on_eeg_fileset_selected(
        self, eeg_fileset: EEGFileset, annotations_file: AnnotationsFile | None = None
    ) -> None:
        self.eeg_fileset = eeg_fileset
        self.data.current_breadcrumbs_element = BreadcrumbsElement.EEG_FILESET
        self.eeg_fileset_selected(eeg_fileset, annotations_file)

    def _on_dataset_expanded(self, dataset: Dataset | None) -> None:
        self.dataset = dataset if dataset is not None else Dataset()

    def _on_eeg_fileset_expanded(self, eeg_fileset: EEGFileset | None) -> None:
        self.eeg_fileset = eeg_fileset if eeg_fileset is not None else EEGFileset()

    def clear_eeg_selection(self) -> None:
        self.eeg_fileset_unselected()

    def clear_dataset_selection(self) -> None:
        self.eeg_fileset = EEGFileset()
        self.clear_eeg_selection()

    def _on_breadcrumbs_navigated(self, target: BreadcrumbsElement) -> None:
        if target == BreadcrumbsElement.ROOT and self.dataset._id is not None:
            self.clear_dataset_selection()
        elif target == BreadcrumbsElement.DATASET and self.eeg_fileset._id is not None:
            self.clear_eeg_selection()

    def step_eeg_selection(self, offset: int) -> None:
        """Navigates to next/previous EEG items, pulling next pages if necessary."""
        eeg_fileset_list = self.data.eeg_fileset_list_state.items
        if not eeg_fileset_list or not offset:
            return

        direction = 1 if offset > 0 else -1
        target_index = self.current_eeg_fileset_index + offset
        target: EEGFileset | None = None

        while 0 <= target_index < len(eeg_fileset_list):
            candidate: EEGFileset = self.ctrl.refresh_eeg_fileset(eeg_fileset_list[target_index])
            if self._matches_eeg_fileset_filter(candidate):
                target = candidate
                break

            target_index += direction

        if target:
            self._on_eeg_fileset_selected(target)

        # Refreshes entire list in the background
        self.fetch_eeg_filesets()

    def select_previous_eeg(self) -> None:
        self.step_eeg_selection(-1)

    def select_next_eeg(self) -> None:
        self.step_eeg_selection(1)

    def _delete_annotations_file(self, annotations_file: AnnotationsFile) -> None:
        if annotations_file.author._id != self._user_state.data._id:
            return

        async def _delete() -> None:
            await to_thread(self.ctrl.delete_annotations_file, annotations_file)
            updated_fileset = await to_thread(self.ctrl.refresh_eeg_fileset, self.eeg_fileset)
            self.update_eeg_fileset_in_list(updated_fileset)

        self.create_async_task(_delete)

    def update_eeg_fileset_in_list(self, updated_fileset: EEGFileset) -> None:
        """Replaces the active item in memory without triggering a full refresh."""
        self.eeg_fileset_list_logic.update_item(updated_fileset)
        self.eeg_fileset = updated_fileset
        if self._matches_eeg_fileset_filter(updated_fileset):
            self.eeg_fileset_list_logic.include_item(updated_fileset._id)
        else:
            self.eeg_fileset_list_logic.exclude_item(updated_fileset._id)

    def set_ui(self, ui: PortalUI) -> None:
        # Toolbar bindings
        ui.refresh_clicked.connect(self.refresh)

        # Dataset bindings
        ui.dataset_list.item_selected.connect(self._on_dataset_selected)
        ui.dataset_list.item_expanded.connect(self._on_dataset_expanded)
        ui.dataset_filters.filter_changed.connect(self.filter_datasets)

        # EEG bindings
        ui.eeg_fileset_list.item_selected.connect(self._on_eeg_fileset_selected)
        ui.eeg_fileset_list.annotation_selected.connect(self._on_eeg_fileset_selected)
        ui.eeg_fileset_list.item_expanded.connect(self._on_eeg_fileset_expanded)
        ui.eeg_fileset_list.annotation_deleted.connect(self._delete_annotations_file)
        ui.eeg_fileset_filters.filter_changed.connect(self.filter_eeg_filesets)
