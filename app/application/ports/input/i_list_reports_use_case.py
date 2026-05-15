from abc import ABC, abstractmethod

from app.application.dto.list_reports_dto import ListReportsInputDTO, ListReportsOutputDTO


class IListReportsUseCase(ABC):
    @abstractmethod
    def execute(self, input_dto: ListReportsInputDTO) -> ListReportsOutputDTO:
        ...
