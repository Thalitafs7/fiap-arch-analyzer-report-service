from fastapi import HTTPException

from app.application.dto.get_report_dto import GetReportInputDTO, GetReportOutputDTO
from app.application.dto.list_reports_dto import ListReportsInputDTO, ListReportsOutputDTO
from app.application.ports.input.i_get_report_use_case import IGetReportUseCase
from app.application.ports.input.i_list_reports_use_case import IListReportsUseCase
from app.domain.exceptions.analysis_not_found import AnalysisNotFoundError


class ReportController:
    def __init__(
        self,
        get_report_use_case: IGetReportUseCase,
        list_reports_use_case: IListReportsUseCase,
    ) -> None:
        self._get_report = get_report_use_case
        self._list_reports = list_reports_use_case

    def handle_get_report(self, analysis_id: str) -> GetReportOutputDTO:
        try:
            return self._get_report.execute(GetReportInputDTO(analysis_id=analysis_id))
        except AnalysisNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    def handle_list_reports(self, limit: int, offset: int) -> ListReportsOutputDTO:
        return self._list_reports.execute(
            ListReportsInputDTO(limit=limit, offset=offset)
        )
