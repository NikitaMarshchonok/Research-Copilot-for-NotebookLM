from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes_health import router as health_router
from app.api.routes_notebooks import router as notebooks_router
from app.api.routes_research import router as research_router
from app.bootstrap import build_container
from app.core.exceptions import AppError
from app.core.logger import setup_logging

container = build_container()
setup_logging(container.settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title=container.settings.app_name, version="0.1.0")
app.include_router(health_router)
app.include_router(notebooks_router)
app.include_router(research_router)


@app.exception_handler(AppError)
def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    logger.warning("Application error: %s", exc)
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(Exception)
def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unexpected error: %s", exc)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
