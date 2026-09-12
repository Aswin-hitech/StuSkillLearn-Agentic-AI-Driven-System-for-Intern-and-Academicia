from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import Base, SessionLocal, engine
from app.routes import router
from app.seed import seed_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI):
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
        title="StuSkillLink — SIH26044",
        description="Agentic AI academia-industry collaboration portal for skill mapping, internships and placement.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix=settings.api_prefix)

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok", "app": settings.app_name, "environment": settings.environment}

    return app


app = create_app()
