from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

from app.domain.entities.report import Report


@dataclass
class ReportDTO:
    id: str
    components_identified: Optional[Any]
    architectural_risks: Optional[Any]
    recommendations: Optional[Any]
    executive_summary: Optional[str]
    rag_used: bool
    qa_is_valid: Optional[bool]
    qa_completeness_score: Optional[float]
    qa_issues_found: Optional[Any]
    qa_quality_notes: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(cls, report: Report) -> ReportDTO:
        return cls(
            id=str(report.id),
            components_identified=report.components_identified,
            architectural_risks=report.architectural_risks,
            recommendations=report.recommendations,
            executive_summary=report.executive_summary,
            rag_used=report.rag_used,
            qa_is_valid=report.qa_is_valid,
            qa_completeness_score=report.qa_completeness_score,
            qa_issues_found=report.qa_issues_found,
            qa_quality_notes=report.qa_quality_notes,
            created_at=report.created_at.isoformat(),
            updated_at=report.updated_at.isoformat(),
        )


@dataclass
class GetReportInputDTO:
    analysis_id: str


@dataclass
class GetReportOutputDTO:
    analysis_id: str
    status: str
    file_name: str
    created_at: str
    report: Optional[ReportDTO]
