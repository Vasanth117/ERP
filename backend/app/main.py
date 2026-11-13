"""FastAPI application."""

from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError

from app import __version__
from app.api.v1.router import api_router
from app.common.context import request_id_var
from app.common.envelope import error_response
from app.core.config import get_settings
from app.core.database import close_mongo, connect_to_mongo, ping_mongo
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.core.redis import close_redis, connect_redis, ping_redis
from app.middleware.rate_limit import LoginRateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    await connect_to_mongo()
    await connect_redis()
    yield
    await close_redis()
    await close_mongo()


def create_app() -> FastAPI:
    settings = get_settings()
    expose_docs = settings.app_env != "production"
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "College ERP API. Obtain tokens from POST /api/v1/auth/login "
            "(optional tenant_code for college users). "
            "Super admins may send X-Tenant-Id to work inside one college."
        ),
        lifespan=lifespan,
        docs_url="/docs" if expose_docs else None,
        redoc_url="/redoc" if expose_docs else None,
        openapi_url="/openapi.json" if expose_docs else None,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(LoginRateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Tenant-Id", "X-Request-Id"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid4())
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers["x-request-id"] = request_id
            return response
        finally:
            request_id_var.reset(token)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        request_id = request.headers.get("x-request-id")
        body = error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = request.headers.get("x-request-id")
        details = [{"loc": list(error["loc"]), "msg": error["msg"]} for error in exc.errors()]
        body = error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=details,
            request_id=request_id,
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=body.model_dump())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        request_id = request.headers.get("x-request-id")
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        body = error_response(code="HTTP_ERROR", message=detail, request_id=request_id)
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(DuplicateKeyError)
    async def duplicate_key_handler(request: Request, _: DuplicateKeyError) -> JSONResponse:
        request_id = request.headers.get("x-request-id")
        body = error_response(
            code="CONFLICT",
            message="A record with these unique values already exists",
            request_id=request_id,
        )
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=body.model_dump())

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready", tags=["health"])
    async def ready() -> dict[str, str]:
        try:
            await ping_mongo()
            await ping_redis()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Dependencies are not ready",
            ) from exc
        return {"status": "ok"}

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
