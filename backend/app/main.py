"""FastAPI application."""

from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import close_mongo, connect_to_mongo, ping_mongo
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    await connect_to_mongo()
    yield
    await close_mongo()


def create_app() -> FastAPI:
    settings = get_settings()
    expose_docs = settings.app_env != "production"
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "College ERP API. Obtain an access token from POST /api/v1/auth/login "
            "and send it as a Bearer token. Super admins may send X-Tenant-Id to "
            "work inside one college."
        ),
        lifespan=lifespan,
        docs_url="/docs" if expose_docs else None,
        redoc_url="/redoc" if expose_docs else None,
        openapi_url="/openapi.json" if expose_docs else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid4())
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response

    @app.exception_handler(DuplicateKeyError)
    async def duplicate_key_handler(_: Request, __: DuplicateKeyError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "A record with these unique values already exists"},
        )

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready", tags=["health"])
    async def ready() -> dict[str, str]:
        try:
            await ping_mongo()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MongoDB is not ready",
            ) from exc
        return {"status": "ok"}

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
