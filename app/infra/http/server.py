from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infra.http.routes.health_routes import router as health_router
from app.infra.http.routes.report_routes import router as report_router
from app.utils.logger import configure_logging, get_logger

configure_logging()
_logger = get_logger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    _logger.info("report_api.startup")
    yield
    _logger.info("report_api.shutdown")


def create_app() -> FastAPI:
    application = FastAPI(
        title="Report API — Hackathon FIAP",
        description="API de consulta de relatórios gerados pelo IA Service.",
        version="1.0.0",
        lifespan=_lifespan,
    )
    application.include_router(health_router)
    application.include_router(report_router)
    return application
