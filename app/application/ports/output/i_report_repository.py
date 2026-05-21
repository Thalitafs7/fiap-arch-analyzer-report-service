from abc import ABC, abstractmethod
from typing import Any, Optional

from app.domain.entities.report import Report


class IReportRepository(ABC):
    @abstractmethod
    def find_by_analysis_id(self, analysis_id: str) -> Optional[Report]:
        ...

    @abstractmethod
    def list_with_analysis(self, limit: int, offset: int) -> list[dict[str, Any]]:
        ...
