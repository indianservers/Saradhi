import asyncio
import hashlib
import logging
import re
from contextlib import asynccontextmanager, suppress
from time import perf_counter
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Request, WebSocket
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from redis.asyncio import Redis
from sqlalchemy import select, text, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

from ai_platform.gateway import ModelGateway
from backend.api.v1.customer_channel import router as customer_channel_router
from backend.api.v1.routes import router
from backend.api.v1.voice import expire_signaling
from backend.api.v1.voice import router as voice_router
from backend.application import identity as identity_service
from backend.application.common import now, scoped
from backend.application.identity import LocalTokenVerifier
from backend.domain.rules import BusinessError
from backend.integrations.maps.routing import UnavailableRoutingProvider
from backend.modules.tracking.realtime import serve_socket
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F
from backend.shared import metrics
from backend.shared.auth import OIDCVerifier, Principal, current_principal
from backend.shared.client_ip import client_ip
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
        app.state.ai_gateway = ModelGateway(settings)
        app.state.engine = create_database(settings)
        app.state.sessions = async_sessionmaker(app.state.engine, expire_on_commit=False)
        app.state.routing_provider = UnavailableRoutingProvider()
        app.state.redis = Redis.from_url(
            settings.redis_url.get_secret_value(),
            socket_connect_timeout=0.25,
            socket_timeout=0.5,
        )
        app.state.token_verifier = (
            LocalTokenVerifier(settings, app.state.sessions)
            if settings.auth_private_key_path
            else OIDCVerifier(settings)
        )
        cleanup = asyncio.create_task(expire_signaling(app.state.sessions))
        try:
            yield
        finally:
            cleanup.cancel()
            with suppress(asyncio.CancelledError):
                await cleanup
            await app.state.ai_gateway.close()
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
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    declared_length = int(content_length)
                except ValueError:
                    response = error(
                        request, 400, "invalid_content_length", "Invalid content length"
                    )
                else:
                    response = (
                        error(
                            request,
                            413,
                            "request_too_large",
                            "Request body exceeds the configured limit",
                        )
                        if declared_length < 0 or declared_length > settings.max_request_body_bytes
                        else None
                    )
            else:
                response = None

            if response is None:
                body = bytearray()
                async for chunk in request.stream():
                    body.extend(chunk)
                    if len(body) > settings.max_request_body_bytes:
                        response = error(
                            request,
                            413,
                            "request_too_large",
                            "Request body exceeds the configured limit",
                        )
                        break
                if response is None:
                    request._body = bytes(body)

            if response is None and (
                request.url.path.startswith("/api/v1/")
                or request.url.path in {"/health/ready", "/health/capabilities"}
            ):
                # A fixed shared PostgreSQL network bucket limits aggregate API
                # traffic across replicas. Separate family budgets protect CPU- or
                # I/O-heavy routes without trusting client-supplied identity headers.
                peer = client_ip(request)
                path = request.url.path
                endpoint, limit = "api", settings.api_requests_per_minute
                if path.startswith("/health/"):
                    endpoint, limit = "health-checks", 120
                elif path.startswith("/api/v1/ai/"):
                    endpoint, limit = "api-ai", 60
                elif path.startswith("/api/v1/bulk/") or path.endswith("customers-export"):
                    endpoint, limit = "api-bulk-export", 20
                elif path == "/api/v1/catalog/products":
                    endpoint, limit = "api-search", 180
                elif path.startswith("/api/v1/auth/"):
                    endpoint, limit = "api-auth", settings.auth_rate_limit_per_minute * 2

                # Unit-only apps with placeholder DB credentials cannot persist a
                # distributed budget; production/staging reject that configuration.
                if "REPLACE_ME" not in settings.database_url.get_secret_value():
                    try:
                        async with request.app.state.sessions.begin() as rate_db:
                            allowed = await identity_service.rate_limit_network(
                                rate_db,
                                peer,
                                endpoint=endpoint,
                                limit=limit,
                            )
                    except Exception:
                        logging.getLogger("quickbuddy").error(
                            "request_throttle_unavailable",
                            extra={"request_id": request.state.request_id},
                        )
                        response = error(
                            request,
                            503,
                            "request_throttling_unavailable",
                            "Request protection is temporarily unavailable",
                        )
                    else:
                        if not allowed:
                            response = error(
                                request,
                                429,
                                "rate_limited",
                                "Request rate limit exceeded; retry after 60 seconds",
                                {"Retry-After": "60"},
                            )
            if response is None:
                response = await call_next(request)
        except Exception:
            logging.getLogger("quickbuddy").error(
                "unhandled_exception", extra={"request_id": request.state.request_id}
            )
            response = error(request, 500, "internal_error", "An internal error occurred")
        route = request.scope.get("route")
        route_path = getattr(route, "path", "unmatched")
        metrics.http_requests.labels(request.method, route_path, str(response.status_code)).inc()
        if response.status_code == 401:
            metrics.security_events.labels("authentication_denied").inc()
        elif response.status_code == 403:
            metrics.security_events.labels("authorization_denied").inc()
        elif response.status_code == 429:
            metrics.security_events.labels("request_throttled").inc()
        metrics.http_request_duration.labels(request.method, route_path).observe(
            perf_counter() - start
        )
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

    @app.get("/metrics", include_in_schema=False)
    async def prometheus_metrics(request: Request):
        if not settings.metrics_enabled:
            return error(request, 404, "not_found", "Metrics are disabled")
        payload, content_type = metrics.render_metrics(app.state.engine.pool)
        return Response(payload, headers={"Content-Type": content_type})

    @app.get("/health/capabilities", operation_id="health_capabilities")
    async def capabilities():
        try:
            async with app.state.engine.connect() as connection:
                postgis = await connection.scalar(
                    text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='postgis')")
                )
                postgres = "ok"
        except Exception:
            postgis, postgres = False, "unavailable"
        try:
            await app.state.redis.ping()
            redis_status = "ok"
        except Exception:
            redis_status = "unavailable"
        routing_status = (
            "unavailable"
            if isinstance(app.state.routing_provider, UnavailableRoutingProvider)
            else "configured"
        )
        return {
            "postgres": postgres,
            "redis": redis_status,
            "postgis": "available" if postgis else "unavailable",
            "road_routing": routing_status,
            "gps_persistence": postgres == "ok",
            "live_cross_instance_events": redis_status == "ok",
            "courier_serviceability": postgis,
        }

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
    app.include_router(customer_channel_router)
    app.include_router(voice_router)

    @app.websocket("/api/v1/realtime")
    async def realtime(websocket: WebSocket, ticket: str, channel: str):
        try:
            kind, raw_id = channel.split(":", 1)
            channel_id = UUID(raw_id) if kind != "system" else None
            if kind not in {"order", "delivery", "pilot", "merchant", "city", "system"}:
                raise ValueError
        except ValueError:
            await websocket.close(code=4400, reason="invalid_channel")
            return
        token_hash = hashlib.sha256(ticket.encode()).hexdigest()
        async with app.state.sessions.begin() as db:
            ticket_model = F["fulfillment.tracking_ws_tickets"]
            ticket_row = await db.scalar(
                update(ticket_model)
                .where(
                    ticket_model.token_hash == token_hash,
                    ticket_model.consumed_at.is_(None),
                    ticket_model.expires_at > now(),
                )
                .values(consumed_at=now())
                .returning(ticket_model)
            )
            if not ticket_row:
                await websocket.close(code=4401, reason="ticket_invalid_or_expired")
                return
            user = await db.get(m.User, ticket_row.user_id)
            if not user or user.status != "active":
                await websocket.close(code=4401, reason="session_revoked")
                return
            roles = set(
                (
                    await db.scalars(
                        select(m.Role.name)
                        .join(m.RoleAssignment)
                        .where(m.RoleAssignment.user_id == user.id)
                    )
                ).all()
            )
            actor = Principal(str(user.id), frozenset(roles))
            try:
                if kind == "order":
                    order = await db.get(m.Order, channel_id)
                    if not order or order.user_id != user.id:
                        raise PermissionError
                    topic = f"order:{channel_id}"
                elif kind == "pilot":
                    pilot = await db.scalar(select(m.Pilot).where(m.Pilot.id == channel_id))
                    if not pilot or pilot.user_id != user.id:
                        raise PermissionError
                    topic = f"pilot:{channel_id}"
                elif kind == "delivery":
                    task = await db.get(m.DeliveryTask, channel_id)
                    if not task:
                        raise PermissionError
                    unit = await db.get(m.FulfillmentUnit, task.fulfillment_unit_id)
                    child = await db.get(m.MerchantOrder, unit.merchant_order_id)
                    order = await db.get(m.Order, child.order_id)
                    pilot = await db.scalar(select(m.Pilot).where(m.Pilot.user_id == user.id))
                    is_assigned = bool(
                        pilot
                        and await db.scalar(
                            select(m.Assignment.id)
                            .where(
                                m.Assignment.task_id == task.id, m.Assignment.pilot_id == pilot.id
                            )
                            .limit(1)
                        )
                    )
                    if order.user_id != user.id and not is_assigned:
                        branch = await db.get(m.Branch, child.branch_id)
                        await scoped(
                            db,
                            actor,
                            "dispatch.write",
                            branch.organization_id,
                            branch.city_id,
                            branch.id,
                        )
                    topic = f"delivery:{channel_id}"
                elif kind == "merchant":
                    await scoped(db, actor, "merchant.write", channel_id)
                    topic = f"merchant:{channel_id}"
                elif kind == "city":
                    await scoped(db, actor, "dispatch.write", city_id=channel_id)
                    topic = f"city:{channel_id}"
                else:
                    if "platform_super_admin" not in roles:
                        raise PermissionError
                    topic = "system"
            except Exception:
                await websocket.close(code=4403, reason="channel_forbidden")
                return
            user_id = user.id

        async def still_authorized():
            async with app.state.sessions() as session:
                current_user = await session.get(m.User, user_id)
                if not current_user or current_user.status != "active":
                    return False
                current_roles = set(
                    (
                        await session.scalars(
                            select(m.Role.name)
                            .join(m.RoleAssignment)
                            .where(m.RoleAssignment.user_id == user_id)
                        )
                    ).all()
                )
                current_actor = Principal(str(user_id), frozenset(current_roles))
                try:
                    if kind == "order":
                        current_order = await session.get(m.Order, channel_id)
                        return bool(current_order and current_order.user_id == user_id)
                    if kind == "pilot":
                        current_pilot = await session.scalar(
                            select(m.Pilot).where(m.Pilot.id == channel_id)
                        )
                        return bool(current_pilot and current_pilot.user_id == user_id)
                    if kind == "delivery":
                        current_task = await session.get(m.DeliveryTask, channel_id)
                        if not current_task:
                            return False
                        current_unit = await session.get(
                            m.FulfillmentUnit, current_task.fulfillment_unit_id
                        )
                        current_child = await session.get(
                            m.MerchantOrder, current_unit.merchant_order_id
                        )
                        current_order = await session.get(m.Order, current_child.order_id)
                        current_pilot = await session.scalar(
                            select(m.Pilot).where(m.Pilot.user_id == user_id)
                        )
                        assigned = bool(
                            current_pilot
                            and await session.scalar(
                                select(m.Assignment.id)
                                .where(
                                    m.Assignment.task_id == current_task.id,
                                    m.Assignment.pilot_id == current_pilot.id,
                                )
                                .limit(1)
                            )
                        )
                        if current_order.user_id == user_id or assigned:
                            return True
                        current_branch = await session.get(m.Branch, current_child.branch_id)
                        await scoped(
                            session,
                            current_actor,
                            "dispatch.write",
                            current_branch.organization_id,
                            current_branch.city_id,
                            current_branch.id,
                        )
                        return True
                    if kind == "merchant":
                        await scoped(session, current_actor, "merchant.write", channel_id)
                        return True
                    if kind == "city":
                        await scoped(session, current_actor, "dispatch.write", city_id=channel_id)
                        return True
                    return "platform_super_admin" in current_roles
                except Exception:
                    return False

        try:
            await app.state.redis.ping()
        except Exception:
            await websocket.close(code=1013, reason="realtime_degraded")
            return
        metrics.websocket_connections.inc()
        try:
            await serve_socket(
                websocket,
                app.state.redis,
                topic,
                f"quickbuddy:realtime:connections:{user.id}",
                settings.tracking_websocket_max_connections,
                still_authorized,
            )
        finally:
            metrics.websocket_connections.dec()

    return app


app = create_app()
