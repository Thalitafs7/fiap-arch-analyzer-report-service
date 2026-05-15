from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import UUID


@dataclass
class Report:
    id: UUID
    analysis_id: UUID
    components_identified: Optional[Any]
    architectural_risks: Optional[Any]
    recommendations: Optional[Any]
    executive_summary: Optional[str]
    rag_used: bool
    qa_is_valid: Optional[bool]
    qa_completeness_score: Optional[float]
    qa_issues_found: Optional[Any]
    qa_quality_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
