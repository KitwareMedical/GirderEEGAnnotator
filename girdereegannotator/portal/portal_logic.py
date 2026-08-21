from asyncio import Task

from trame_server import Server
from undo_stack import Signal

from girdereegannotator.database.models import (
    AnnotationStatus,
    Dataset,
    EEGFileset,
    User,
)
from girdereegannotator.portal.components.filters.annotator_filter import Annotator
from girdereegannotator.portal.components.filters.status_filter import Status
from girdereegannotator.utils.base_logic import BaseLogic
from girdereegannotator.utils.load_status import LoadStatus

from .components.breadcrumbs import BreadcrumbsElement
from .paginated_list_logic import PaginatedListLogic
from .portal_ui import PortalState, PortalUI


class PortalLogic(BaseLogic[PortalState]):
    eeg_fileset_selected = Signal(EEGFileset | None)
    eeg_fileset_unselected = Signal()
    select_eeg_fileset = Signal(int)

    def __init__(self, server: Server) -> None:
        super().__init__(server, PortalState)
        self.current_dataset = self.get_sub_state(self.name.current_dataset)
        self.current_eeg_fileset = self.get_sub_state(self.name.current_eeg_fileset)
        self.current_user_id = None

        self.dataset_list_logic = PaginatedListLogic[Dataset](
            server,
            self.get_sub_state(self.name.dataset_list_state),
            load_callable=self.ctrl.list_datasets,
        )

        self.eeg_fileset_list_logic = PaginatedListLogic[EEGFileset](
            server,
            self.get_sub_state(self.name.eeg_fileset_list_state),
            load_callable=self.ctrl.list_eeg_filesets,
            filter_callable=self._matches_eeg_fileset_filter,
            count_all_callable=self._count_all_eeg_filesets,
        )

    def _count_all_eeg_filesets(self, eeg_fileset_list: list[EEGFileset]) -> None:
        total = len(eeg_fileset_list)
        validated = sum(f.validated for f in eeg_fileset_list)

        self.data.eeg_fileset_filter_state.status_state.counts = {
            Status.UNDEFINED: total,
            Status.VALIDATED: validated,
            Status.TO_ANNOTATE: total - validated,
            Status.TO_VALIDATE: sum(
                any(ann.status == AnnotationStatus.TO_VALIDATE for ann in f.annotations) for f in eeg_fileset_list
            ),
        }

    def _matches_eeg_fileset_filter(self, eeg_fileset: EEGFileset) -> bool:
        status = self.data.eeg_fileset_filter_state.status_state.status
        annotator = self.data.eeg_fileset_filter_state.annotator_state.annotator

        if status == Status.VALIDATED and not eeg_fileset.validated:
            return False
        if status != Status.VALIDATED and eeg_fileset.validated:
            return False

        annotations = eeg_fileset.annotations
        if status == Status.TO_VALIDATE:
            annotations = [ann for ann in annotations if ann.status == AnnotationStatus.TO_VALIDATE]

        if annotator == Annotator.ME:
            return any(ann.annotator_id == self.current_user_id for ann in annotations)
        if annotator == Annotator.NOT_ME:
            return any(ann.annotator_id != self.current_user_id for ann in annotations)

        return status != Status.TO_VALIDATE or bool(annotations)

    def fetch_datasets(self, reset: bool = True) -> Task | None:
        if reset:
            self.dataset_list_logic.reset()
            self.dataset_list_logic.count_items(search_text=self.data.dataset_filter_state.search_text)

        return self.dataset_list_logic.append_list_items(search_text=self.data.dataset_filter_state.search_text)

    def fetch_eeg_filesets(self, reset: bool = True) -> Task | None:
        if self.current_dataset.data._id is None:
            return None

        dataset = self.current_dataset.get_dataclass()
        if reset:
            # Reset state for UI to visually refresh
            self.data.eeg_fileset_filter_state.status_state.counts = {}
            self.eeg_fileset_list_logic.reset()

            self.eeg_fileset_list_logic.count_items(
                dataset=dataset,
                search_text=self.data.eeg_fileset_filter_state.search_state.search_text,
            )

        return self.eeg_fileset_list_logic.append_list_items(
            dataset=dataset,
            search_text=self.data.eeg_fileset_filter_state.search_state.search_text,
        )

    def refresh(self) -> None:
        """Reloads the active view from scratch."""
        if self.current_dataset.data._id is None:
            self.fetch_datasets()
        else:
            self.fetch_eeg_filesets()

    def clear_eeg_selection(self) -> None:
        self.current_eeg_fileset.set_dataclass(EEGFileset())
        self.eeg_fileset_unselected()

    def clear_dataset_selection(self) -> None:
        self.current_dataset.set_dataclass(Dataset())
        self.clear_eeg_selection()

        # Wiping filters and counts when switching datasets
        self.data.eeg_fileset_filter_state.status_state.counts = {}
        self.data.eeg_fileset_filter_state.status_state.status = Status.UNDEFINED
        self.data.eeg_fileset_filter_state.annotator_state.annotator = Annotator.UNDEFINED

        self.eeg_fileset_list_logic.reset()

    def _on_breadcrumb_navigated(self, target: BreadcrumbsElement) -> None:
        if target == BreadcrumbsElement.ROOT:
            self.clear_dataset_selection()
        elif target == BreadcrumbsElement.DATASET:
            self.clear_eeg_selection()

    def _on_dataset_selected(self, dataset: Dataset) -> None:
        self.current_dataset.set_dataclass(dataset)
        self.fetch_eeg_filesets()

    def _on_eeg_fileset_selected(self, eeg_fileset: EEGFileset) -> None:
        self.current_eeg_fileset.set_dataclass(eeg_fileset)
        self.eeg_fileset_selected(eeg_fileset)

    def _on_status_filter_changed(self, status: Status) -> None:
        self.data.eeg_fileset_filter_state.annotator_state.annotator = (
            Annotator.NOT_ME if status == Status.TO_VALIDATE else Annotator.UNDEFINED
        )
        self.fetch_eeg_filesets()

    async def step_eeg_selection(self, offset: int) -> None:
        """Navigates to next/previous EEG items, pulling next pages if necessary."""
        state = self.data.eeg_fileset_list_state
        if state.current_index is None or not state.items:
            return

        target_index = state.current_index + offset

        while target_index >= len(state.items) and state.load_status == LoadStatus.UNDEFINED:
            task = self.fetch_eeg_filesets(reset=False)
            if task is not None:
                await task

        self.select_eeg_fileset((state.current_index + offset) % len(state.items))

    async def select_previous_eeg(self) -> None:
        await self.step_eeg_selection(-1)

    async def select_next_eeg(self) -> None:
        await self.step_eeg_selection(1)

    def update_eeg_fileset_in_list(self, updated_fileset: EEGFileset) -> None:
        """Replaces the active item in memory without triggering a network reload."""
        self.current_eeg_fileset.set_dataclass(updated_fileset)
        idx = self.data.eeg_fileset_list_state.current_index
        if idx is not None:
            self.data.eeg_fileset_list_state.items[idx] = updated_fileset

    def set_current_user(self, user: User) -> None:
        self.current_user_id = user._id

    def set_ui(self, ui: PortalUI) -> None:
        # Toolbar bindings
        ui.refresh_clicked.connect(self.refresh)
        ui.breadcrumbs_ui.breadcrumbs_clicked.connect(self._on_breadcrumb_navigated)

        # Dataset bindings
        ui.dataset_list.item_selected.connect(self._on_dataset_selected)
        ui.dataset_filters.search_clicked.connect(self.fetch_datasets)
        ui.dataset_list.set_load_callback(lambda: self.fetch_datasets(reset=False))

        # EEG bindings
        ui.eeg_fileset_list.item_selected.connect(self._on_eeg_fileset_selected)
        ui.eeg_fileset_filters.annotator_updated.connect(self.fetch_eeg_filesets)
        ui.eeg_fileset_filters.search_clicked.connect(self.fetch_eeg_filesets)
        ui.eeg_fileset_filters.status_clicked.connect(self._on_status_filter_changed)
        ui.eeg_fileset_list.set_load_callback(lambda: self.fetch_eeg_filesets(reset=False))

        self.select_eeg_fileset.connect(ui.eeg_fileset_list.select_item)
