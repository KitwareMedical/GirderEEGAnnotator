from asyncio import Task
from collections.abc import Callable

from trame_server import Server
from undo_stack import Signal

from girdereegannotator.database.models import (
    AnnotationStatus,
    Dataset,
    EEGFileset,
    User,
)
from girdereegannotator.portal.components.expandable_list import ExpandableListState
from girdereegannotator.portal.components.filters.annotator_filter import Annotator
from girdereegannotator.portal.components.filters.status_filter import Status
from girdereegannotator.utils.base_logic import BaseLogic
from girdereegannotator.utils.load_status import LoadStatus

from .components.breadcrumbs import BreadcrumbsElement
from .portal_ui import PortalState, PortalUI


class PortalLogic(BaseLogic[PortalState]):
    eeg_fileset_selected = Signal(EEGFileset | None)
    eeg_fileset_unselected = Signal()
    select_eeg_fileset = Signal(int)
    reset_dataset_scroll = Signal()
    reset_eeg_fileset_scroll = Signal()

    def __init__(self, server: Server) -> None:
        super().__init__(server, PortalState)
        self.current_dataset = self.get_sub_state(self.name.current_dataset)
        self.current_eeg_fileset = self.get_sub_state(self.name.current_eeg_fileset)

        self.current_user_id = None
        self.limit = 15
        self._eeg_filesets_database_offset = 0
        self._eeg_filesets_exhausted = False

    def set_current_user(self, user: User) -> None:
        self.current_user_id = user._id

    def _load_next_list_item(
        self,
        list_state: ExpandableListState,
        load_callable: Callable[[], list],
        **kwargs,
    ) -> Task | None:
        if list_state.load_status == LoadStatus.LOADING:
            return None

        list_state.load_status = LoadStatus.LOADING

        def _refresh() -> None:
            try:
                item_list = load_callable(limit=self.limit, **kwargs)
                list_state.load_status = (
                    LoadStatus.LOADED if not self.limit or len(item_list) < self.limit else LoadStatus.UNDEFINED
                )
                list_state.items = list_state.items + item_list

            except Exception as e:
                list_state.load_status = LoadStatus.ERROR
                list_state.status_message = str(e)

        return self.create_async_task(_refresh)

    def _refresh_dataset_list(self) -> None:
        self.data.dataset_list_state.items = []
        self.data.dataset_list_state.current_index = None
        self.data.dataset_list_state.load_status = LoadStatus.UNDEFINED
        self.data.dataset_list_state.status_message = None
        self._load_next_datasets()

    def _refresh_eeg_fileset_list(self) -> None:
        self.data.eeg_fileset_list_state.items = []
        self.data.eeg_fileset_list_state.current_index = None
        self.data.eeg_fileset_list_state.load_status = LoadStatus.UNDEFINED
        self.data.eeg_fileset_list_state.status_message = None

        self._eeg_filesets_exhausted = False
        self._eeg_filesets_database_offset = 0

        self._load_next_eeg_filesets()

    def _load_next_datasets(self) -> Task | None:
        return self._load_next_list_item(
            self.data.dataset_list_state,
            self.server.controller.list_datasets,
            offset=len(self.data.dataset_list_state.items),
            search_text=self.data.dataset_filter_state.search_text,
        )

    def _load_next_eeg_filesets(self) -> Task | None:
        if self.current_dataset.data._id is None:
            return None

        self.data.eeg_fileset_filter_state.status_state.counts = dict.fromkeys(Status, 0)
        return self._load_next_list_item(
            self.data.eeg_fileset_list_state,
            self._load_filtered_eeg_filesets,
            dataset=self.current_dataset.get_dataclass(),
            search_text=self.data.eeg_fileset_filter_state.search_state.search_text,
        )

    def _load_filtered_eeg_filesets(self, limit: int, **kwargs) -> list[EEGFileset]:
        result: list[EEGFileset] = []

        while len(result) < limit and not self._eeg_filesets_exhausted:
            item_list = self.server.controller.list_eeg_filesets(
                offset=self._eeg_filesets_database_offset,
                limit=limit,
                **kwargs,
            )

            if not item_list:
                self._eeg_filesets_exhausted = True
                break

            self._eeg_filesets_database_offset += len(item_list)

            result.extend(
                eeg_fileset
                for eeg_fileset in item_list
                if self._matches_eeg_fileset_filter(
                    eeg_fileset,
                    self.data.eeg_fileset_filter_state.status_state.status,
                    self.data.eeg_fileset_filter_state.annotator_state.annotator,
                )
            )

            if len(item_list) < limit:
                self._eeg_filesets_exhausted = True

        return result[:limit]

    def _matches_eeg_fileset_filter(
        self,
        eeg_fileset: EEGFileset,
        status: Status,
        annotator: Annotator,
    ) -> bool:
        if status == Status.VALIDATED and not eeg_fileset.validated:
            return False

        if status != Status.VALIDATED and eeg_fileset.validated:
            return False

        annotations = eeg_fileset.annotations
        if status == Status.TO_VALIDATE:
            annotations = (ann for ann in annotations if ann.status == AnnotationStatus.TO_VALIDATE)

        if annotator == Annotator.ME:
            return any(ann.annotator_id == self.current_user_id for ann in annotations)

        if annotator == Annotator.NOT_ME:
            return any(ann.annotator_id != self.current_user_id for ann in annotations)

        return status != Status.TO_VALIDATE or any(annotations)

    def _reset_eeg_fileset(self) -> None:
        self.current_eeg_fileset.set_dataclass(EEGFileset())
        self.eeg_fileset_unselected()

    def _reset_dataset(self) -> None:
        self.current_dataset.set_dataclass(Dataset())
        self._reset_eeg_fileset()
        self._refresh_eeg_fileset_list()

    def _on_breadcrumbs_clicked(self, breadcrumbs_element: BreadcrumbsElement) -> None:
        if breadcrumbs_element == BreadcrumbsElement.ROOT:
            self._reset_dataset()

        elif breadcrumbs_element == BreadcrumbsElement.DATASET:
            self._reset_eeg_fileset()

    def _on_dataset_selected(self, dataset: Dataset) -> None:
        self.current_dataset.set_dataclass(dataset)
        self._load_next_eeg_filesets()

    def _on_eeg_fileset_selected(self, eeg_fileset: EEGFileset) -> None:
        self.current_eeg_fileset.set_dataclass(eeg_fileset)
        self.eeg_fileset_selected(eeg_fileset)

    def _on_eeg_fileset_status_clicked(self) -> None:
        if self.data.eeg_fileset_filter_state.status_state.status == Status.VALIDATED:
            self.data.eeg_fileset_filter_state.annotator_state.annotator = Annotator.UNDEFINED

        elif self.data.eeg_fileset_filter_state.status_state.status == Status.TO_VALIDATE:
            self.data.eeg_fileset_filter_state.annotator_state.annotator = Annotator.NOT_ME

        self._refresh_eeg_fileset_list()

    async def _shift_eeg_fileset_index(self, offset: int) -> None:
        if self.data.eeg_fileset_list_state.current_index is None or not self.data.eeg_fileset_list_state.items:
            return

        target_index = self.data.eeg_fileset_list_state.current_index + offset

        while (
            target_index >= len(self.data.eeg_fileset_list_state.items)
            and self.data.eeg_fileset_list_state.load_status == LoadStatus.UNDEFINED
        ):
            refresh_task = self._load_next_eeg_filesets()
            if refresh_task is not None:
                await refresh_task

        self.select_eeg_fileset(
            (self.data.eeg_fileset_list_state.current_index + offset) % len(self.data.eeg_fileset_list_state.items)
        )

    async def select_previous_eeg(self) -> None:
        await self._shift_eeg_fileset_index(-1)

    async def select_next_eeg(self) -> None:
        await self._shift_eeg_fileset_index(1)

    def update_eeg_fileset_list(self, eeg_fileset: EEGFileset) -> None:
        self.current_eeg_fileset.set_dataclass(eeg_fileset)
        self.data.eeg_fileset_list_state.items = [
            eeg_fileset if index == self.data.eeg_fileset_list_state.current_index else media
            for (index, media) in enumerate(self.data.eeg_fileset_list_state.items)
        ]

    def refresh(self) -> None:
        if self.current_dataset.data._id is None:
            self._refresh_dataset_list()
        else:
            self._refresh_eeg_fileset_list()

    def set_ui(self, ui: PortalUI) -> None:
        ui.refresh_clicked.connect(self.refresh)
        ui.breadcrumbs_ui.breadcrumbs_clicked.connect(self._on_breadcrumbs_clicked)

        ui.dataset_list.item_selected.connect(self._on_dataset_selected)
        ui.dataset_filters.search_clicked.connect(self._refresh_dataset_list)
        ui.dataset_list.set_load_callback(self._load_next_datasets)

        ui.eeg_fileset_list.item_selected.connect(self._on_eeg_fileset_selected)
        ui.eeg_fileset_filters.annotator_updated.connect(self._refresh_eeg_fileset_list)
        ui.eeg_fileset_filters.search_clicked.connect(self._refresh_eeg_fileset_list)
        ui.eeg_fileset_filters.status_clicked.connect(self._on_eeg_fileset_status_clicked)
        ui.eeg_fileset_list.set_load_callback(self._load_next_eeg_filesets)

        self.select_eeg_fileset.connect(ui.eeg_fileset_list.select_item)
