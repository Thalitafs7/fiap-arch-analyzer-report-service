from fastapi import APIRouter

from app.infra.database.connection import check_db_connection

router = APIRouter()


@router.get("/health")
def health_check():
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "db": "connected" if db_ok else "unavailable",
    }
