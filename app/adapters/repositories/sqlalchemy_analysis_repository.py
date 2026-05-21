from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.adapters.mappers.analysis_mapper import AnalysisMapper
from app.application.ports.output.i_analysis_repository import IAnalysisRepository
from app.domain.entities.analysis import Analysis


class SqlAlchemyAnalysisRepository(IAnalysisRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def find_by_id(self, analysis_id: str) -> Optional[Analysis]:
        row = self._db.execute(
            text("SELECT * FROM analyses WHERE id = :id"),
            {"id": analysis_id},
        ).mappings().first()
        if row is None:
            return None
        return AnalysisMapper.to_domain(dict(row))
