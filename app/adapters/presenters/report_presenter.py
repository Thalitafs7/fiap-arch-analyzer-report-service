from dataclasses import asdict

from app.application.dto.get_report_dto import GetReportOutputDTO
from app.application.dto.list_reports_dto import ListReportsOutputDTO


class ReportPresenter:
    @staticmethod
    def to_get_response(output: GetReportOutputDTO) -> dict:
        return {
            "analysis_id": output.analysis_id,
            "status": output.status,
            "file_name": output.file_name,
            "created_at": output.created_at,
            "report": asdict(output.report) if output.report else None,
        }

    @staticmethod
    def to_list_response(output: ListReportsOutputDTO) -> dict:
        return {
            "total": output.total,
            "limit": output.limit,
            "offset": output.offset,
            "items": [asdict(item) for item in output.items],
        }
