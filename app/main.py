"""
Instagram Reel Downloader — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger
from app.models.schemas import ErrorResponse
from app.routes.download import router


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown logic."""
    logger.info(
        "Starting %s v%s | downloads_dir=%s",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.DOWNLOADS_DIR,
    )
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "A production-ready REST API for downloading Instagram Reels. "
            "POST a reel URL to `/download` and receive the video file directly."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # -----------------------------------------------------------------------
    # CORS
    # NOTE: allow_credentials=True is incompatible with allow_origins=["*"].
    # Starlette raises ValueError at startup when both are set together.
    # We enable credentials only when explicit origins are configured.
    # -----------------------------------------------------------------------
    wildcard_origins = settings.ALLOWED_ORIGINS == ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=not wildcard_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # -----------------------------------------------------------------------
    # Global exception handlers
    # -----------------------------------------------------------------------

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        logger.warning("Validation error | path=%s error=%s", request.url.path, exc)
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="VALIDATION_ERROR",
                message=str(exc),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception | path=%s", request.url.path)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred. Please try again later.",
            ).model_dump(),
        )

    # -----------------------------------------------------------------------
    # Routers
    # -----------------------------------------------------------------------
    app.include_router(router, prefix="/api/v1")

    return app


app = create_app()
