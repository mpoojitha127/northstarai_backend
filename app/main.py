from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, chat, dashboard, goals
from app.core.config import settings
from app.db.database import Base, engine

# MVP schema management: create_all on startup. Swap for Alembic migrations
# before this touches a production Postgres instance with real user data --
# create_all cannot handle schema changes safely once there's data to preserve.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Strategic Decision Intelligence Layer -- API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(goals.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": settings.APP_NAME, "environment": settings.ENVIRONMENT}
