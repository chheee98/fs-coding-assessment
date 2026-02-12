# Backend Task 2: Todo CRUD Endpoints

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement 6 Todo CRUD endpoints with schemas, repository, service, and dependency injection following the existing User pattern.

**Architecture:** Layer-by-layer — schemas first (data contracts), then repository (DB queries), then service (business logic + ownership checks), then dependency injection, then router wiring. Each layer depends on the previous.

**Tech Stack:** FastAPI, SQLModel, Pydantic, PostgreSQL (asyncpg)

---

## Quick Context

The router stubs exist but return placeholder strings. The repository and service are empty classes. You need to build the full stack: schemas → repository → service → dependency → router.

**Depends on:** Task 1 (needs `user_id` FK on Todo model)
**Blocks:** Task 3 (stats reuses repository/service), Task 4 (tests call these endpoints)

## New Libraries

None.

## Project Structure (Before → After)

```
backend/
  app/
    schemas/
      ~ todo.py              # Was "# TODO" comment → full schemas
    repositories/
      ~ todo_repository.py   # Was empty class → full CRUD methods
    services/
      ~ todo_service.py      # Was empty class → business logic
    dependencies/
      + todo.py              # New: TodoServiceDep
    routers/
      ~ todos.py             # Was stubs → fully wired endpoints
```

## Acceptance Criteria

- [ ] `POST /api/v1/todos` — creates todo, returns 201, auto-assigns `user_id`
- [ ] `GET /api/v1/todos` — returns paginated list, hides description for non-owners, supports `page`, `page_size`, `priority`, `completed`, `search` query params
- [ ] `GET /api/v1/todos/{todo_id}` — returns full todo for owner, 403 for non-owner, 404 if not found
- [ ] `PATCH /api/v1/todos/{todo_id}` — partial update for owner only, 403 for non-owner
- [ ] `DELETE /api/v1/todos/{todo_id}` — deletes for owner only, returns 204, 403 for non-owner
- [ ] `PATCH /api/v1/todos/{todo_id}/complete` — toggles completed status, owner only
- [ ] All endpoints require Bearer token authentication
- [ ] Pagination response includes `items`, `total`, `page`, `page_size`, `total_pages`
- [ ] Search is case-insensitive partial match on title
- [ ] All functions have type hints and docstrings
- [ ] Proper HTTP status codes (201, 200, 204, 403, 404, 422)

---

## Implementation

### Step 1: Create `app/schemas/todo.py`

This defines all request/response shapes. Built on top of `TodoBase` from the model.

```python
import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field

from app.models.todo import Priority, TodoStatus


class TodoCreate(SQLModel):
    """Schema for creating a new todo."""

    title: str = Field(max_length=200)
    description: str = Field(default="")
    priority: Priority | None = None
    due_date: datetime | None = None


class TodoUpdate(SQLModel):
    """Schema for updating a todo. All fields optional for partial updates."""

    title: str | None = Field(default=None, max_length=200)
    description: str | None = None
    status: TodoStatus | None = None
    priority: Priority | None = None
    due_date: datetime | None = None


class TodoRead(SQLModel):
    """Full todo response — returned for owner access."""

    id: uuid.UUID
    title: str
    description: str
    status: TodoStatus
    priority: Priority | None
    due_date: datetime | None
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TodoReadList(SQLModel):
    """Todo in list view — description is None for non-owner todos."""

    id: uuid.UUID
    title: str
    description: str | None
    status: TodoStatus
    priority: Priority | None
    due_date: datetime | None
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TodoPaginatedResponse(SQLModel):
    """Paginated response wrapper."""

    items: list[TodoReadList]
    total: int
    page: int
    page_size: int
    total_pages: int
```

**Explanation:**
- `TodoCreate` — only fields the user provides. No `id`, `user_id`, `status`, `created_at` (those are auto-set).
- `TodoUpdate` — all `Optional` for PATCH partial updates.
- `TodoRead` — full detail for single-todo owner access.
- `TodoReadList` — `description: str | None` so the service can null it for non-owners.
- `TodoPaginatedResponse` — wraps list results with pagination metadata.

**Trade-off:** Separate `TodoRead` vs `TodoReadList` instead of one schema with optional description. This makes the API contract explicit — the list endpoint always returns `TodoReadList`, the detail endpoint always returns `TodoRead`. Clearer for the frontend.

### Step 2: Create `app/repositories/todo_repository.py`

Handles all database queries. Follows the same pattern as `UserRepository`.

```python
import uuid

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.todo import Priority, Todo, TodoStatus


class TodoRepository:
    """Repository for Todo database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, todo: Todo) -> Todo:
        """Create a new todo in the database."""
        self.session.add(todo)
        await self.session.commit()
        await self.session.refresh(todo)
        return todo

    async def get_by_id(self, todo_id: uuid.UUID) -> Todo | None:
        """Get a single todo by ID."""
        return await self.session.get(Todo, todo_id)

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        priority: Priority | None = None,
        completed: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Todo], int]:
        """Get all todos with pagination, filtering, and search.

        Returns a tuple of (todos, total_count).
        """
        statement = select(Todo)

        # Apply filters
        if priority is not None:
            statement = statement.where(Todo.priority == priority)
        if completed is not None:
            if completed:
                statement = statement.where(Todo.status == TodoStatus.COMPLETED)
            else:
                statement = statement.where(Todo.status != TodoStatus.COMPLETED)
        if search is not None:
            statement = statement.where(Todo.title.ilike(f"%{search}%"))

        # Count total before pagination
        count_statement = select(func.count()).select_from(statement.subquery())
        count_result = await self.session.exec(count_statement)
        total = count_result.one()

        # Apply pagination
        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size).order_by(Todo.created_at.desc())

        result = await self.session.exec(statement)
        todos = list(result.all())

        return todos, total

    async def update(self, todo: Todo) -> Todo:
        """Update an existing todo."""
        self.session.add(todo)
        await self.session.commit()
        await self.session.refresh(todo)
        return todo

    async def delete(self, todo: Todo) -> None:
        """Delete a todo from the database."""
        await self.session.delete(todo)
        await self.session.commit()
```

**Explanation:**
- `get_all` returns `tuple[list[Todo], int]` — the items and total count. The service needs both to build the paginated response.
- Filters are chained with `.where()` — each filter is independently optional.
- `completed` param is a boolean that maps to `TodoStatus.COMPLETED` vs everything else (as decided in brainstorm).
- `search` uses `ilike` for case-insensitive partial match (as decided in brainstorm).
- `order_by(Todo.created_at.desc())` — newest first, sensible default.

**Trade-off:** Counting via subquery (`select(func.count()).select_from(...)`) adds one extra query but gives accurate total even with filters applied. Using `.count()` on the ORM result would require loading all rows into memory.

### Step 3: Create `app/services/todo_service.py`

Business logic layer — handles ownership checks and description hiding.

```python
import math
import uuid

from fastapi import HTTPException, status

from app.models.todo import Priority, Todo, TodoStatus
from app.repositories.todo_repository import TodoRepository
from app.schemas.todo import (
    TodoCreate,
    TodoPaginatedResponse,
    TodoRead,
    TodoReadList,
    TodoUpdate,
)


class TodoService:
    """Service for Todo business logic."""

    def __init__(self, todo_repository: TodoRepository) -> None:
        self.todo_repository = todo_repository

    async def create_todo(self, todo_in: TodoCreate, user_id: uuid.UUID) -> TodoRead:
        """Create a new todo for the authenticated user."""
        todo = Todo(
            **todo_in.model_dump(),
            user_id=user_id,
        )
        todo = await self.todo_repository.create(todo)
        return TodoRead.model_validate(todo)

    async def get_todos(
        self,
        current_user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        priority: Priority | None = None,
        completed: bool | None = None,
        search: str | None = None,
    ) -> TodoPaginatedResponse:
        """Get all todos with pagination. Hides description for non-owner todos."""
        todos, total = await self.todo_repository.get_all(
            page=page,
            page_size=page_size,
            priority=priority,
            completed=completed,
            search=search,
        )

        items = []
        for todo in todos:
            item = TodoReadList.model_validate(todo)
            if todo.user_id != current_user_id:
                item.description = None
            items.append(item)

        total_pages = math.ceil(total / page_size) if page_size > 0 else 0

        return TodoPaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_todo(self, todo_id: uuid.UUID, current_user_id: uuid.UUID) -> TodoRead:
        """Get a single todo. Only the owner can access."""
        todo = await self._get_todo_or_404(todo_id)
        self._check_owner(todo, current_user_id)
        return TodoRead.model_validate(todo)

    async def update_todo(
        self, todo_id: uuid.UUID, todo_in: TodoUpdate, current_user_id: uuid.UUID
    ) -> TodoRead:
        """Update a todo. Only the owner can update."""
        todo = await self._get_todo_or_404(todo_id)
        self._check_owner(todo, current_user_id)

        update_data = todo_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(todo, key, value)

        todo = await self.todo_repository.update(todo)
        return TodoRead.model_validate(todo)

    async def delete_todo(self, todo_id: uuid.UUID, current_user_id: uuid.UUID) -> None:
        """Delete a todo. Only the owner can delete."""
        todo = await self._get_todo_or_404(todo_id)
        self._check_owner(todo, current_user_id)
        await self.todo_repository.delete(todo)

    async def toggle_complete(self, todo_id: uuid.UUID, current_user_id: uuid.UUID) -> TodoRead:
        """Toggle todo completion status.

        If not completed -> mark as COMPLETED.
        If already completed -> mark as NOT_STARTED.
        """
        todo = await self._get_todo_or_404(todo_id)
        self._check_owner(todo, current_user_id)

        if todo.status == TodoStatus.COMPLETED:
            todo.status = TodoStatus.NOT_STARTED
        else:
            todo.status = TodoStatus.COMPLETED

        todo = await self.todo_repository.update(todo)
        return TodoRead.model_validate(todo)

    async def _get_todo_or_404(self, todo_id: uuid.UUID) -> Todo:
        """Get a todo by ID or raise 404."""
        todo = await self.todo_repository.get_by_id(todo_id)
        if not todo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Todo not found",
            )
        return todo

    @staticmethod
    def _check_owner(todo: Todo, current_user_id: uuid.UUID) -> None:
        """Raise 403 if the current user is not the todo owner."""
        if todo.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this todo",
            )
```

**Explanation:**
- `create_todo` — spreads `TodoCreate` fields + injects `user_id` from auth.
- `get_todos` — gets all todos, then nulls out `description` at service layer for non-owners (as decided in brainstorm).
- `_get_todo_or_404` and `_check_owner` — private helpers to DRY up the ownership pattern used in get/update/delete/complete.
- `toggle_complete` — `COMPLETED ↔ NOT_STARTED`, any status can go to COMPLETED (as decided in brainstorm).
- `model_validate` converts ORM model to Pydantic schema (SQLModel built-in).

**Trade-off:** Description hiding happens in Python, not SQL. Slightly less efficient but far more readable and testable. For a todo app's data volume, this is negligible.

### Step 4: Create `app/dependencies/todo.py`

Dependency injection — follows the exact same pattern as `app/dependencies/user.py`.

```python
from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_async_session
from app.repositories.todo_repository import TodoRepository
from app.services.todo_service import TodoService


def get_todo_service(
    session: AsyncSession = Depends(get_async_session),
) -> TodoService:
    """Dependency to get TodoService with injected repository."""
    todo_repository = TodoRepository(session)
    return TodoService(todo_repository)


TodoServiceDep = Annotated[TodoService, Depends(get_todo_service)]
```

### Step 5: Rewrite `app/routers/todos.py`

Wire everything together. Note: `/stats` route must be defined BEFORE `/{todo_id}` to avoid FastAPI matching "stats" as a UUID path parameter.

```python
import uuid

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDep
from app.dependencies.todo import TodoServiceDep
from app.models.todo import Priority
from app.schemas.todo import (
    TodoCreate,
    TodoPaginatedResponse,
    TodoRead,
    TodoUpdate,
)


router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
async def create_todo(
    todo_in: TodoCreate,
    todo_service: TodoServiceDep,
    current_user: CurrentUserDep,
) -> TodoRead:
    """Create a new todo for the authenticated user."""
    return await todo_service.create_todo(todo_in, current_user.id)


@router.get("", response_model=TodoPaginatedResponse)
async def get_todos(
    todo_service: TodoServiceDep,
    current_user: CurrentUserDep,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    priority: Priority | None = Query(default=None, description="Filter by priority"),
    completed: bool | None = Query(default=None, description="Filter by completed status"),
    search: str | None = Query(default=None, min_length=1, description="Search by title"),
) -> TodoPaginatedResponse:
    """Get all todos with pagination, filtering, and search.

    All authenticated users can see all todos, but description
    is hidden for todos not owned by the current user.
    """
    return await todo_service.get_todos(
        current_user_id=current_user.id,
        page=page,
        page_size=page_size,
        priority=priority,
        completed=completed,
        search=search,
    )


@router.get("/stats")
async def get_stats(
    todo_service: TodoServiceDep,
    current_user: CurrentUserDep,
):
    """Get statistics for the authenticated user's todos.

    Note: Implementation in Task 3.
    """
    # Placeholder — will be implemented in Task 3
    return {"message": "stats endpoint placeholder"}


@router.get("/{todo_id}", response_model=TodoRead)
async def get_todo(
    todo_id: uuid.UUID,
    todo_service: TodoServiceDep,
    current_user: CurrentUserDep,
) -> TodoRead:
    """Get a single todo by ID. Only the owner can access full details."""
    return await todo_service.get_todo(todo_id, current_user.id)


@router.patch("/{todo_id}", response_model=TodoRead)
async def update_todo(
    todo_id: uuid.UUID,
    todo_in: TodoUpdate,
    todo_service: TodoServiceDep,
    current_user: CurrentUserDep,
) -> TodoRead:
    """Update a todo. Only the owner can update. Supports partial updates."""
    return await todo_service.update_todo(todo_id, todo_in, current_user.id)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: uuid.UUID,
    todo_service: TodoServiceDep,
    current_user: CurrentUserDep,
) -> None:
    """Delete a todo. Only the owner can delete."""
    await todo_service.delete_todo(todo_id, current_user.id)


@router.patch("/{todo_id}/complete", response_model=TodoRead)
async def complete_todo(
    todo_id: uuid.UUID,
    todo_service: TodoServiceDep,
    current_user: CurrentUserDep,
) -> TodoRead:
    """Toggle todo completion status.

    If not completed -> mark as COMPLETED.
    If already completed -> mark as NOT_STARTED.
    """
    return await todo_service.toggle_complete(todo_id, current_user.id)
```

**Critical: Route ordering.** The `/stats` endpoint is defined BEFORE `/{todo_id}`. If reversed, FastAPI would try to parse "stats" as a UUID and return 422. This is a common FastAPI gotcha.

**Explanation of query params:**
- `page` and `page_size` have validation (`ge=1`, `le=100`)
- `priority` uses the `Priority` enum directly — FastAPI auto-validates
- `completed` is `bool | None` — maps to status filter in repository
- `search` has `min_length=1` to avoid empty searches

### Step 6: Verify manually

```bash
# Start the server
uv run uvicorn app.main:app --reload

# Open http://localhost:8000/docs
# 1. Register a user via POST /api/v1/auth/register
# 2. Login via POST /api/v1/auth/login → copy the access_token
# 3. Click "Authorize" button → paste Bearer token
# 4. Test each endpoint
```

### Step 7: Commit

```bash
git add app/schemas/todo.py app/repositories/todo_repository.py app/services/todo_service.py app/dependencies/todo.py app/routers/todos.py
git commit -m "feat: implement Todo CRUD endpoints with pagination, filtering, and search"
```
