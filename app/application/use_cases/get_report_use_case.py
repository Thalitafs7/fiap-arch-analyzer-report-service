from app.application.dto.get_report_dto import GetReportInputDTO, GetReportOutputDTO, ReportDTO
from app.application.ports.input.i_get_report_use_case import IGetReportUseCase
from app.application.ports.output.i_analysis_repository import IAnalysisRepository
from app.application.ports.output.i_report_repository import IReportRepository
from app.domain.exceptions.analysis_not_found import AnalysisNotFoundError


class GetReportUseCase(IGetReportUseCase):
    def __init__(
        self,
        analysis_repository: IAnalysisRepository,
        report_repository: IReportRepository,
    ) -> None:
        self._analysis_repository = analysis_repository
        self._report_repository = report_repository

    def execute(self, input_dto: GetReportInputDTO) -> GetReportOutputDTO:
        analysis = self._analysis_repository.find_by_id(input_dto.analysis_id)
        if analysis is None:
            raise AnalysisNotFoundError(input_dto.analysis_id)

        report = self._report_repository.find_by_analysis_id(input_dto.analysis_id)

        return GetReportOutputDTO(
            analysis_id=str(analysis.id),
            status=analysis.status.value,
            file_name=analysis.file_name,
            created_at=analysis.created_at.isoformat(),
            report=ReportDTO.from_entity(report) if report else None,
        )
