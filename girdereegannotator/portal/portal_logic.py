from asyncio import Task
from collections.abc import Callable

from trame_server import Server
from undo_stack import Signal

from girdereegannotator.database.models import BIDSDataset, EEGFileset
from girdereegannotator.portal.components.expandable_list import (
    ExpandableListState,
    LoadResult,
)
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

        self.limit = 15

    def _load_next_list_item(
        self,
        list_state: ExpandableListState,
        load_callable: Callable[[], list],
        **kwargs,
    ) -> Task | None:
        if self.data.load_status == LoadStatus.LOADING:
            return None

        self.data.load_status = LoadStatus.LOADING

        def _refresh() -> None:
            try:
                item_list = load_callable(offset=len(list_state.items), limit=self.limit, **kwargs)
                list_state.load_result = LoadResult.MORE if len(item_list) == self.limit else LoadResult.EMPTY
                list_state.items = list_state.items + item_list

                self.data.load_status = LoadStatus.UNDEFINED

            except Exception as e:
                self.data.load_status = LoadStatus.ERROR
                self.data.status_message = str(e)

        return self.create_async_task(_refresh)

    def _refresh_dataset_list(self) -> None:
        self.data.dataset_list_state.items = []
        self.data.dataset_list_state.current_index = None
        self.data.dataset_list_state.load_result = LoadResult.MORE
        self._load_next_datasets()

    def _refresh_eeg_fileset_list(self) -> None:
        self.data.eeg_fileset_list_state.items = []
        self.data.eeg_fileset_list_state.current_index = None
        self.data.eeg_fileset_list_state.load_result = LoadResult.MORE
        self._load_next_eeg_filesets()

    def _load_next_datasets(self) -> Task | None:
        return self._load_next_list_item(
            self.data.dataset_list_state,
            self.server.controller.list_datasets,
        )

    def _load_next_eeg_filesets(self) -> Task | None:
        if self.current_dataset.data._id is None:
            return None

        return self._load_next_list_item(
            self.data.eeg_fileset_list_state,
            self.server.controller.list_eeg_filesets,
            dataset=self.current_dataset.get_dataclass(),
        )

    def _reset_eeg_fileset(self) -> None:
        self.current_eeg_fileset.set_dataclass(EEGFileset())
        self.eeg_fileset_unselected()

    def _reset_dataset(self) -> None:
        self.current_dataset.set_dataclass(BIDSDataset())
        self._reset_eeg_fileset()
        self._refresh_eeg_fileset_list()

    def _on_breadcrumbs_clicked(self, breadcrumbs_element: BreadcrumbsElement) -> None:
        if breadcrumbs_element == BreadcrumbsElement.ROOT:
            self._reset_dataset()

        elif breadcrumbs_element == BreadcrumbsElement.DATASET:
            self._reset_eeg_fileset()

    def _on_dataset_selected(self, dataset: BIDSDataset) -> None:
        self.current_dataset.set_dataclass(dataset)
        self._load_next_eeg_filesets()

    def _on_eeg_fileset_selected(self, eeg_fileset: EEGFileset) -> None:
        self.current_eeg_fileset.set_dataclass(eeg_fileset)
        self.eeg_fileset_selected(eeg_fileset)

    async def _shift_eeg_fileset_index(self, offset: int) -> None:
        if self.data.eeg_fileset_list_state.current_index is None or not self.data.eeg_fileset_list_state.items:
            return

        if (self.data.eeg_fileset_list_state.current_index + offset) == len(
            self.data.eeg_fileset_list_state.items
        ) and self.data.eeg_fileset_list_state.load_result == LoadResult.MORE:
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
        ui.eeg_fileset_list.item_selected.connect(self._on_eeg_fileset_selected)

        ui.dataset_list.set_load_callback(self._load_next_datasets)
        ui.eeg_fileset_list.set_load_callback(self._load_next_eeg_filesets)

        self.select_eeg_fileset.connect(ui.eeg_fileset_list.select_item)
