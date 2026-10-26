import asyncio
import logging
import re
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api.v1.routes import router
from backend.application.identity import LocalTokenVerifier
from backend.domain.rules import BusinessError
from backend.shared.auth import OIDCVerifier, Principal, current_principal
from backend.shared.contracts import ErrorBody, ErrorResponse, Health, PrincipalView
from backend.shared.database import create_database, session_scope
from backend.shared.logging import configure_logging
from backend.shared.settings import Settings, get_settings


async def get_session(request: Request):
    async with session_scope(request.app.state.sessions) as session:
        yield session


async def probe_database(engine, settings):
    if "REPLACE_ME" in settings.database_url.get_secret_value():
        raise RuntimeError("Database credentials not configured")
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def dependencies_ready(app):
    async def probe(name, operation):
        try:
            await asyncio.wait_for(operation(), timeout=4)
            return name, "ok"
        except Exception:
            return name, "unavailable"

    return dict(
        await asyncio.gather(
            probe("postgresql", lambda: probe_database(app.state.engine, app.state.settings)),
            probe("redis", app.state.redis.ping),
        )
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging()

    @asynccontextmanager
    async def lifespan(app):
        app.state.settings = settings
        app.state.engine = create_database(settings)
        app.state.sessions = async_sessionmaker(app.state.engine, expire_on_commit=False)
        app.state.redis = Redis.from_url(
            settings.redis_url.get_secret_value(), socket_connect_timeout=2, socket_timeout=2
        )
        app.state.token_verifier = (
            LocalTokenVerifier(settings, app.state.sessions)
            if settings.auth_private_key_path
            else OIDCVerifier(settings)
        )
        yield
        await app.state.redis.aclose()
        await app.state.engine.dispose()

    app = FastAPI(
        title="Quickbuddy API",
        version="0.2.0",
        lifespan=lifespan,
        responses={code: {"model": ErrorResponse} for code in [401, 403, 404, 422, 500, 503]},
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    @app.middleware("http")
    async def context(request: Request, call_next):
        incoming = request.headers.get("X-Request-ID", "")
        request.state.request_id = (
            incoming if re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", incoming) else str(uuid4())
        )
        start = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logging.getLogger("quickbuddy").error(
                "unhandled_exception", extra={"request_id": request.state.request_id}
            )
            response = error(request, 500, "internal_error", "An internal error occurred")
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        if settings.app_env != "production":
            response.headers["X-Quickbuddy-Environment"] = settings.app_env
        logging.getLogger("quickbuddy").info(
            "http_request",
            extra={
                "request_id": request.state.request_id,
                "status": response.status_code,
                "duration_ms": round((perf_counter() - start) * 1000, 2),
            },
        )
        return response

    def error(request, status, code, message, headers=None):
        body = ErrorResponse(
            error=ErrorBody(code=code, message=message, request_id=request.state.request_id)
        )
        return JSONResponse(status_code=status, content=body.model_dump(), headers=headers)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        return error(
            request, exc.status_code, f"http_{exc.status_code}", str(exc.detail), exc.headers
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return error(request, 422, "validation_error", "Request validation failed")

    @app.exception_handler(BusinessError)
    async def business_error(request, exc):
        headers = (
            {"Retry-After": "60"}
            if exc.status == 429
            else {"WWW-Authenticate": "Bearer"}
            if exc.status == 401
            else None
        )
        return error(request, exc.status, exc.code, exc.message, headers)

    @app.exception_handler(IntegrityError)
    async def integrity_error(request, exc):
        return error(
            request, 409, "integrity_conflict", "Operation conflicts with a data integrity rule"
        )

    @app.exception_handler(DBAPIError)
    async def database_error(request, exc):
        sqlstate = getattr(exc.orig, "sqlstate", None)
        if sqlstate in {"40P01", "40001"}:
            return error(
                request,
                409,
                "transaction_retry",
                "Retry the whole operation with the same idempotency key",
            )
        return error(
            request, 503, "database_unavailable", "Database operation could not be completed"
        )

    @app.get("/health/live", response_model=Health, operation_id="health_live")
    async def live():
        return Health(status="ok")

    @app.get(
        "/health/ready",
        response_model=Health,
        responses={503: {"model": Health}},
        operation_id="health_ready",
    )
    async def ready():
        checks = await dependencies_ready(app)
        healthy = all(v == "ok" for v in checks.values())
        return JSONResponse(
            status_code=200 if healthy else 503,
            content=Health(
                status="ready" if healthy else "not_ready", dependencies=checks
            ).model_dump(),
        )

    @app.get("/api/v1/me", response_model=PrincipalView, operation_id="get_me")
    async def me(principal: Annotated[Principal, Depends(current_principal)]):
        return PrincipalView(subject=principal.subject, roles=sorted(principal.roles))

    app.include_router(router)
    return app


app = create_app()
