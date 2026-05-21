from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.analysis import Analysis


class IAnalysisRepository(ABC):
    @abstractmethod
    def find_by_id(self, analysis_id: str) -> Optional[Analysis]:
        ...
