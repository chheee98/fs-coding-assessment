"""Pytest configuration and shared fixtures for async API testing."""

import asyncio
import os
import sys
import uuid
from pathlib import Path
from typing import AsyncGenerator

import pytest
from dotenv import load_dotenv
from faker import Faker
from httpx import ASGITransport, AsyncClient
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load test-specific env — NOT the main .env
load_dotenv(project_root / ".env.test")

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise ValueError(
        "TEST_DATABASE_URL must be set in .env.test. "
        "Copy .env.test.example to .env.test and configure your test database."
    )

from app.main import app
from app.db.session import get_async_session, verify_connection

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def verify_db():
    """Verify test DB connection once at session start."""
    try:
        await verify_connection(target_engine=test_engine, db_url=TEST_DATABASE_URL)
    except ConnectionError as e:
        pytest.exit(str(e), returncode=1)


@pytest.fixture(scope="class", autouse=True)
async def setup_database():
    """Create all tables before each test class, drop after. Clean slate per class."""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
    """Override the app's session dependency with test database session."""
    async with AsyncSession(test_engine) as session:
        yield session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client that talks to the app with test DB."""
    app.dependency_overrides[get_async_session] = get_test_session
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def fake() -> Faker:
    """Faker instance for generating test data."""
    return Faker()


@pytest.fixture
async def auth_user(client: AsyncClient) -> dict:
    """Register a user and return user info + auth headers."""
    unique = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"testuser_{unique}",
        "email": f"test_{unique}@example.com",
        "password": "Password123!",
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    user = register_response.json()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": user_data["username"], "password": user_data["password"]},
    )
    token = login_response.json()["access_token"]
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "user": user,
    }


@pytest.fixture
async def second_auth_user(client: AsyncClient) -> dict:
    """Register a SECOND user and return user info + auth headers. For cross-user testing."""
    unique = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"otheruser_{unique}",
        "email": f"other_{unique}@example.com",
        "password": "Password123!",
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    user = register_response.json()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": user_data["username"], "password": user_data["password"]},
    )
    token = login_response.json()["access_token"]
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "user": user,
    }