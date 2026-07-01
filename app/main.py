"""FastAPI application entrypoint for the Welfare Management System."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import admin, auth, donor, food, fund, problem
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.database.session import SessionLocal, create_tables
from app.services.admin_service import ensure_admin_exists

configure_logging()
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    logger.info("Database tables created / verified.")

    db = SessionLocal()
    try:
        ensure_admin_exists(db)
        logger.info("Admin account ready.")
    finally:
        db.close()

    yield


app = FastAPI(
    title=settings.app_name,
    description="A platform connecting donors and those in need — blood, funds, rashan & counseling.",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(donor.router)
app.include_router(fund.router)
app.include_router(food.router)
app.include_router(problem.router)
app.include_router(admin.router)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=FileResponse)
def serve_frontend() -> FileResponse:
    return FileResponse(str(TEMPLATES_DIR / "index.html"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}
