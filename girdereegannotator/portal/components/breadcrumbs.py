from enum import Enum, auto

from trame.widgets import html
from trame.widgets import vuetify3 as v3


class BreadcrumbsElement(Enum):
    ROOT = auto()
    DATASET = auto()
    EEG_FILESET = auto()


class Breadcrumbs(html.Div):
    def __init__(self, current_breadcrumbs_element: str, dataset_name: str, eeg_fileset_name: str, **kwargs):
        super().__init__(classes="button-bar", **kwargs)
        self.current_element = current_breadcrumbs_element

        with self:
            self._build_breadcrumbs_button(
                breadcrumbs_element=BreadcrumbsElement.ROOT,
                icon="mdi-home",
            )
            v3.VIcon(
                v_if=self._has_breadcrumbs_element(BreadcrumbsElement.DATASET), disabled=True, icon="mdi-chevron-right"
            )
            self._build_breadcrumbs_button(
                breadcrumbs_element=BreadcrumbsElement.DATASET,
                text=(dataset_name,),
            )
            v3.VIcon(
                v_if=self._has_breadcrumbs_element(BreadcrumbsElement.EEG_FILESET),
                disabled=True,
                icon="mdi-chevron-right",
            )
            self._build_breadcrumbs_button(
                breadcrumbs_element=BreadcrumbsElement.EEG_FILESET,
                text=(eeg_fileset_name,),
            )

    def _build_breadcrumbs_button(self, breadcrumbs_element: BreadcrumbsElement, **kwargs) -> None:
        v3.VBtn(
            v_if=self._has_breadcrumbs_element(breadcrumbs_element),
            classes="breadcrumbs-button",
            active=self._is_breadcrumbs_element(breadcrumbs_element),
            active_color=(f"{self._is_breadcrumbs_element(breadcrumbs_element)} ? 'primary' : 'undefined'",),
            click=self._set_breadcrumbs_element(breadcrumbs_element),
            density="compact",
            ripple=False,
            variant="plain",
            **kwargs,
        )

    def _has_breadcrumbs_element(self, breadcrumbs_element: BreadcrumbsElement) -> str:
        return f"({self.current_element} >=  {breadcrumbs_element.value})"

    def _is_breadcrumbs_element(self, breadcrumbs_element: BreadcrumbsElement) -> str:
        return f"({self.current_element} ===  {breadcrumbs_element.value})"

    def _set_breadcrumbs_element(self, breadcrumbs_element: BreadcrumbsElement) -> str:
        return f"{self.current_element} =  {breadcrumbs_element.value}"
