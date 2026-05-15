from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AnalysisId:
    value: UUID

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def from_string(cls, raw: str) -> AnalysisId:
        return cls(value=UUID(raw))
