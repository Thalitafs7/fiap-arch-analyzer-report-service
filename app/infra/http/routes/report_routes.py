from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.adapters.controllers.report_controller import ReportController
from app.adapters.presenters.report_presenter import ReportPresenter
from app.adapters.repositories.sqlalchemy_analysis_repository import SqlAlchemyAnalysisRepository
from app.adapters.repositories.sqlalchemy_report_repository import SqlAlchemyReportRepository
from app.application.use_cases.get_report_use_case import GetReportUseCase
from app.application.use_cases.list_reports_use_case import ListReportsUseCase
from app.infra.database.connection import get_db

router = APIRouter()


def _build_controller(db: Session) -> ReportController:
    analysis_repo = SqlAlchemyAnalysisRepository(db)
    report_repo = SqlAlchemyReportRepository(db)
    return ReportController(
        get_report_use_case=GetReportUseCase(analysis_repo, report_repo),
        list_reports_use_case=ListReportsUseCase(report_repo),
    )


@router.get("/reports/{analysis_id}")
def get_report(analysis_id: str, db: Session = Depends(get_db)):
    controller = _build_controller(db)
    output = controller.handle_get_report(analysis_id)
    return ReportPresenter.to_get_response(output)


@router.get("/reports")
def list_reports(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    controller = _build_controller(db)
    output = controller.handle_list_reports(limit=limit, offset=offset)
    return ReportPresenter.to_list_response(output)
