from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.value_objects.analysis_id import AnalysisId
from app.domain.value_objects.analysis_status import AnalysisStatus


@dataclass
class Analysis:
    id: AnalysisId
    status: AnalysisStatus
    file_name: str
    file_type: Optional[str]
    s3_key: Optional[str]
    sqs_message_id: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
