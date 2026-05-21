from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.adapters.mappers.report_mapper import ReportMapper
from app.application.ports.output.i_report_repository import IReportRepository
from app.domain.entities.report import Report


class SqlAlchemyReportRepository(IReportRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def find_by_analysis_id(self, analysis_id: str) -> Optional[Report]:
        row = self._db.execute(
            text(
                "SELECT * FROM reports WHERE analysis_id = :id "
                "ORDER BY created_at DESC LIMIT 1"
            ),
            {"id": analysis_id},
        ).mappings().first()
        if row is None:
            return None
        return ReportMapper.to_domain(dict(row))

    def list_with_analysis(self, limit: int, offset: int) -> list[dict[str, Any]]:
        rows = self._db.execute(
            text("""
                SELECT r.*, a.status, a.file_name, a.created_at AS analysis_created_at
                FROM reports r
                JOIN analyses a ON r.analysis_id = a.id
                ORDER BY r.created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"limit": limit, "offset": offset},
        ).mappings().all()
        return [dict(r) for r in rows]
