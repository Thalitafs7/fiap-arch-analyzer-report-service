from app.domain.exceptions.base import DomainException


class AnalysisNotFoundError(DomainException):
    def __init__(self, analysis_id: str) -> None:
        super().__init__(f"Análise '{analysis_id}' não encontrada.")
        self.analysis_id = analysis_id
