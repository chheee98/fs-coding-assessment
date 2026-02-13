"""Main FastAPI application module."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import auth, todos, users

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify database connection on startup
    from app.db.session import verify_connection
    await verify_connection()

    yield
    print("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Todo management API with authentication",
    version="1.0.0",
    lifespan=lifespan,
    openapi_url="/openapi.json",
)


# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(todos.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Todo API is running!", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
