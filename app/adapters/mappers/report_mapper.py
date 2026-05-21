from typing import Any
from uuid import UUID

from app.domain.entities.report import Report


class ReportMapper:
    @staticmethod
    def to_domain(row: dict[str, Any]) -> Report:
        return Report(
            id=UUID(str(row["id"])),
            analysis_id=UUID(str(row["analysis_id"])),
            components_identified=row.get("components_identified"),
            architectural_risks=row.get("architectural_risks"),
            recommendations=row.get("recommendations"),
            executive_summary=row.get("executive_summary"),
            rag_used=bool(row.get("rag_used", False)),
            qa_is_valid=row.get("qa_is_valid"),
            qa_completeness_score=row.get("qa_completeness_score"),
            qa_issues_found=row.get("qa_issues_found"),
            qa_quality_notes=row.get("qa_quality_notes"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
