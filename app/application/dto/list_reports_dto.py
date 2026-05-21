from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ReportSummaryDTO:
    id: str
    analysis_id: str
    executive_summary: Optional[str]
    qa_is_valid: Optional[bool]
    qa_completeness_score: Optional[float]
    status: str
    file_name: str
    analysis_created_at: str
    created_at: str

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> ReportSummaryDTO:
        return cls(
            id=str(row["id"]),
            analysis_id=str(row["analysis_id"]),
            executive_summary=row.get("executive_summary"),
            qa_is_valid=row.get("qa_is_valid"),
            qa_completeness_score=row.get("qa_completeness_score"),
            status=str(row["status"]),
            file_name=str(row["file_name"]),
            analysis_created_at=str(row.get("analysis_created_at", "")),
            created_at=str(row["created_at"]),
        )


@dataclass
class ListReportsInputDTO:
    limit: int
    offset: int


@dataclass
class ListReportsOutputDTO:
    total: int
    limit: int
    offset: int
    items: list[ReportSummaryDTO]
