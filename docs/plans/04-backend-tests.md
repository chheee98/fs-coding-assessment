# Backend Task 4: Write Test Cases

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Write `test_create_todo_success` and `test_get_all_todos` in `tests/test_todos.py` with a proper async test setup using Docker Compose PostgreSQL.

**Architecture:** Set up async test fixtures in `conftest.py` (test database, async client, auth helpers). Write the two required tests. The test database is a separate database (`todo_db_test`) in the same Docker Compose PostgreSQL container.

**Tech Stack:** pytest, pytest-asyncio, httpx (AsyncClient), SQLModel, PostgreSQL, Docker Compose

---

## Quick Context

The assessment requires exactly two named tests: `test_create_todo_success` and `test_get_all_todos`. The existing `conftest.py` only adds the project root to `sys.path`. The existing `test_main.py` uses sync `TestClient` — our tests need async `AsyncClient` because the app uses async database sessions.

**Depends on:** Task 1 (FK), Task 2 (CRUD endpoints), Task 3 (optional, stats not tested here)

## New Libraries

**`aiosqlite`** — No. We use the real PostgreSQL test database (Docker Compose) as decided in brainstorm.

None needed — `httpx` and `pytest-asyncio` are already in dev dependencies.

## Project Structure (Before → After)

```
backend/
  ~ compose.yaml          # Add init script for test DB creation
  + db-init/
    + init-test-db.sh     # Script to create todo_db_test
  ~ tests/conftest.py     # Full async test setup
  ~ tests/test_todos.py   # Two required test cases
```

## Acceptance Criteria

- [ ] `uv run pytest tests/test_todos.py -v` passes
- [ ] `test_create_todo_success` — creates todo with auth, asserts 201 + correct fields
- [ ] `test_get_all_todos` — two users create todos, asserts description hidden for non-owner, asserts `user_id` present
- [ ] Tests use real PostgreSQL (`todo_db_test`) via Docker Compose
- [ ] Tests clean up after themselves (tables created/dropped per session)
- [ ] Tests don't depend on each other (isolated)

---

## Implementation

### Step 1: Create `backend/db-init/init-test-db.sh`

This init script runs when the PostgreSQL container starts for the first time. It creates the test database alongside the main one.

```bash
#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE todo_db_test;
EOSQL
```

### Step 2: Update `backend/compose.yaml`

Mount the init script so PostgreSQL creates both databases on startup.

```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: todo-db
    environment:
      POSTGRES_DB: todo_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: 5up3r53cr3t
    ports:
      - "5432:5432"
    volumes:
      - ./db-init:/docker-entrypoint-initdb.d
```

**Explanation:** PostgreSQL automatically runs scripts in `/docker-entrypoint-initdb.d/` on first start. This creates `todo_db_test` alongside `todo_db`.

**Important:** If your container already exists, you need to remove its volume for the init script to run:

```bash
docker compose down -v
docker compose up -d
```

### Step 3: Rewrite `backend/tests/conftest.py`

Full async test setup with real PostgreSQL.

```python
"""Pytest configuration and shared fixtures for async API testing."""

import asyncio
import sys
import uuid
from pathlib import Path
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import app
from app.db.session import get_async_session

# Test database URL — same Postgres container, different database
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:5up3r53cr3t@localhost:5432/todo_db_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Create all tables at the start, drop at the end."""
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
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register a user and return auth headers with Bearer token."""
    unique = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"testuser_{unique}",
        "email": f"test_{unique}@example.com",
        "password": "Password123!",
    }
    await client.post("/api/v1/auth/register", json=user_data)

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": user_data["username"], "password": user_data["password"]},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def second_auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register a SECOND user and return auth headers. For testing cross-user behavior."""
    unique = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"otheruser_{unique}",
        "email": f"other_{unique}@example.com",
        "password": "Password123!",
    }
    await client.post("/api/v1/auth/register", json=user_data)

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": user_data["username"], "password": user_data["password"]},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

**Explanation:**
- `test_engine` points to `todo_db_test` — real PostgreSQL, separate from dev data.
- `setup_database` — session-scoped, creates tables once, drops them at the end.
- `get_test_session` — overrides FastAPI's `get_async_session` dependency so the app uses the test DB.
- `client` — `httpx.AsyncClient` with `ASGITransport` (standard way to test async FastAPI apps).
- `auth_headers` / `second_auth_headers` — register unique users per test (UUID in username avoids collisions). Returns headers dict ready for use.

**Trade-off:** Session-scoped table creation means test data accumulates across tests. This is fine for our 2 tests. If the test suite grew, you'd want per-test transactions with rollback. For this assessment, simplicity wins.

### Step 4: Write `backend/tests/test_todos.py`

The two required tests.

```python
"""Tests for Todo CRUD endpoints."""

import pytest
from httpx import AsyncClient


class TestTodos:
    """Test cases for todo endpoints."""

    @pytest.mark.asyncio
    async def test_create_todo_success(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ):
        """Test that an authenticated user can create a todo.

        Verifies:
        - Status code is 201
        - Response contains correct data (title, description, priority)
        - Response contains auto-generated fields (id, user_id, status, created_at)
        """
        todo_data = {
            "title": "Test Todo",
            "description": "Test description",
            "priority": "HIGH",
        }

        response = await client.post(
            "/api/v1/todos",
            json=todo_data,
            headers=auth_headers,
        )

        assert response.status_code == 201

        data = response.json()
        assert data["title"] == "Test Todo"
        assert data["description"] == "Test description"
        assert data["priority"] == "HIGH"
        assert data["status"] == "NOT_STARTED"
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_all_todos(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        second_auth_headers: dict[str, str],
    ):
        """Test that an authenticated user can get all todos.

        Verifies:
        - Status code is 200
        - Description is hidden (None) for todos not owned by the current user
        - Todos include user_id to identify owner
        - Pagination metadata is present
        """
        # User 1 creates a todo
        user1_todo = {
            "title": "User 1 Todo",
            "description": "User 1 secret description",
            "priority": "LOW",
        }
        create_response = await client.post(
            "/api/v1/todos",
            json=user1_todo,
            headers=auth_headers,
        )
        user1_todo_id = create_response.json()["user_id"]

        # User 2 creates a todo
        user2_todo = {
            "title": "User 2 Todo",
            "description": "User 2 secret description",
            "priority": "MEDIUM",
        }
        await client.post(
            "/api/v1/todos",
            json=user2_todo,
            headers=second_auth_headers,
        )

        # User 1 gets all todos
        response = await client.get(
            "/api/v1/todos",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        # Verify pagination metadata
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

        items = data["items"]
        assert len(items) >= 2  # At least the 2 todos we just created

        # Every item should have user_id to identify owner
        for item in items:
            assert "user_id" in item

        # Find user 1's todo and user 2's todo
        user1_items = [i for i in items if i["user_id"] == user1_todo_id]
        user2_items = [i for i in items if i["user_id"] != user1_todo_id]

        # User 1's own todos should have description visible
        for item in user1_items:
            assert item["description"] is not None

        # Other users' todos should have description hidden (None)
        for item in user2_items:
            assert item["description"] is None
```

**Explanation:**
- `test_create_todo_success` — straightforward POST with auth, asserts 201 and all expected fields.
- `test_get_all_todos` — creates todos from 2 different users, then User 1 fetches the list. Verifies:
  - User 1's own todos have visible `description`
  - Other users' todos have `description: None`
  - Every item has `user_id` for owner identification
  - Pagination metadata exists

**Note on `user1_todo_id`:** We capture `user_id` from the create response (not `id`) to identify which items belong to User 1 when filtering the list.

### Step 5: Run the tests

```bash
# Make sure Docker Compose is running with test DB
docker compose down -v && docker compose up -d

# Wait a few seconds for PostgreSQL to initialize

# Run the tests
uv run pytest tests/test_todos.py -v
```

**Expected output:**

```
tests/test_todos.py::TestTodos::test_create_todo_success PASSED
tests/test_todos.py::TestTodos::test_get_all_todos PASSED
```

### Step 6: Run full test suite with coverage

```bash
uv run pytest tests/ -v --cov=app --cov-report=term-missing
```

**Expected:** All tests pass (including existing `test_main.py` tests). Coverage >= 70% for todo endpoints.

### Step 7: Commit

```bash
git add db-init/ compose.yaml tests/conftest.py tests/test_todos.py
git commit -m "test: add todo CRUD tests with Docker Compose PostgreSQL test database"
```
