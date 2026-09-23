from __future__ import annotations

from contextlib import asynccontextmanager
import json
import logging
from time import perf_counter
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text
from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory

from app.config import settings
from app.db import Base, SessionLocal, engine
from app.routes import router
from app.admin_routes import router as admin_router
from app.seed import seed_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auto_create_schema:
        Base.metadata.create_all(bind=engine)
    if settings.auto_seed_demo:
        db = SessionLocal()
        try:
            seed_demo_data(db)
        finally:
            db.close()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="StuSkillLink - SIH26044",
        description="Agentic AI academia-industry collaboration portal for skill mapping, internships and placement.",
        version="2.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_host_list)
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    @app.middleware("http")
    async def same_origin_state_changes(request: Request, call_next):
        # Same-origin cookies need a CSRF boundary. Browsers send Origin on state-changing
        # fetch/form requests; reject untrusted origins before authentication is evaluated.
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            if origin and origin not in settings.cors_list:
                return JSONResponse(status_code=403, content={"detail": "Untrusted request origin"})
            cookie_authenticated = bool(
                request.cookies.get(settings.access_cookie_name)
                or request.cookies.get(settings.refresh_cookie_name)
            ) and not request.headers.get("authorization")
            if settings.is_production and cookie_authenticated and not origin:
                return JSONResponse(status_code=403, content={"detail": "Origin header required for cookie-authenticated state changes"})
        return await call_next(request)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        started = perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.url.path.startswith(settings.api_prefix):
            response.headers["Cache-Control"] = "no-store"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        logging.getLogger("stuskilllink.access").info(json.dumps({
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round((perf_counter() - started) * 1000, 2),
        }))
        return response

    app.include_router(router, prefix=settings.api_prefix)
    app.include_router(admin_router, prefix=settings.api_prefix)

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok", "app": settings.app_name, "environment": settings.environment, "version": "2.0.0"}

    @app.get("/ready", tags=["health"])
    def readiness():
        checks = {"database": "unknown", "redis": "optional", "migrations": "not-required"}
        migration_ready = not settings.is_production
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                checks["database"] = "ok"
                if settings.is_production:
                    revision = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar_one_or_none()
                    alembic_path = Path(__file__).resolve().parents[1] / "alembic.ini"
                    config = AlembicConfig(str(alembic_path))
                    expected = ScriptDirectory.from_config(config).get_current_head()
                    if revision and expected and revision == expected:
                        checks["migrations"] = "ok"
                        migration_ready = True
                    elif not revision:
                        checks["migrations"] = "missing"
                    else:
                        checks["migrations"] = f"outdated:{revision or 'none'}->{expected or 'unknown'}"
        except Exception:
            checks["database"] = "failed"
            if settings.is_production:
                checks["migrations"] = "failed"
                migration_ready = False
        try:
            from redis import Redis
            Redis.from_url(settings.redis_url, socket_connect_timeout=0.25, socket_timeout=0.25).ping()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "unavailable"
        ready = checks["database"] == "ok" and (not settings.is_production or (checks["redis"] == "ok" and migration_ready))
        payload = {"status": "ready" if ready else "degraded", "checks": checks}
        return JSONResponse(status_code=200 if ready else 503, content=payload)

    return app


app = create_app()
