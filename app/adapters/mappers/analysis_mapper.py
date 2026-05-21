import logging
from typing import Any

from app.domain.entities.analysis import Analysis
from app.domain.value_objects.analysis_id import AnalysisId
from app.domain.value_objects.analysis_status import AnalysisStatus

logger = logging.getLogger(__name__)


class AnalysisMapper:
    @staticmethod
    def to_domain(row: dict[str, Any]) -> Analysis:
        try:
            status = AnalysisStatus(row["status"])
        except ValueError:
            logger.warning(
                "Status desconhecido no banco: '%s'. Usando ERROR como fallback.",
                row["status"],
            )
            status = AnalysisStatus.ERROR

        return Analysis(
            id=AnalysisId.from_string(str(row["id"])),
            status=status,
            file_name=str(row["file_name"]),
            file_type=row.get("file_type"),
            s3_key=row.get("s3_key"),
            sqs_message_id=row.get("sqs_message_id"),
            error_message=row.get("error_message"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
