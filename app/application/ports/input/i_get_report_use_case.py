from abc import ABC, abstractmethod

from app.application.dto.get_report_dto import GetReportInputDTO, GetReportOutputDTO


class IGetReportUseCase(ABC):
    @abstractmethod
    def execute(self, input_dto: GetReportInputDTO) -> GetReportOutputDTO:
        ...
