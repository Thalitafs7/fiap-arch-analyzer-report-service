from app.infra.database.connection import get_engine
from app.infra.http.server import create_app

get_engine()

app = create_app()
