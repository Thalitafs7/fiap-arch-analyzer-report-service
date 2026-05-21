from app.application.dto.list_reports_dto import (
    ListReportsInputDTO,
    ListReportsOutputDTO,
    ReportSummaryDTO,
)
from app.application.ports.input.i_list_reports_use_case import IListReportsUseCase
from app.application.ports.output.i_report_repository import IReportRepository


class ListReportsUseCase(IListReportsUseCase):
    def __init__(self, report_repository: IReportRepository) -> None:
        self._report_repository = report_repository

    def execute(self, input_dto: ListReportsInputDTO) -> ListReportsOutputDTO:
        rows = self._report_repository.list_with_analysis(
            limit=input_dto.limit,
            offset=input_dto.offset,
        )
        items = [ReportSummaryDTO.from_row(row) for row in rows]
        return ListReportsOutputDTO(
            total=len(items),
            limit=input_dto.limit,
            offset=input_dto.offset,
            items=items,
        )
