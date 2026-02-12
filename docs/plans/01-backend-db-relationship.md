# Backend Task 1: Database Relationship — Todo ↔ User

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a foreign key from `Todo` to `User` so every todo belongs to a user.

**Architecture:** Add `user_id` UUID column with FK constraint and index on the `todo` table. Use SQLModel `Relationship` for ORM-level navigation in both directions. Generate a new Alembic migration — never edit the existing initial migration.

**Tech Stack:** SQLModel, Alembic, PostgreSQL

---

## Quick Context

The `Todo` table currently has no link to `User`. Every other backend task depends on this — ownership checks (Task 2), stats filtering (Task 3), and tests (Task 4) all need `user_id` on the todo. This is the foundation.

**Depends on:** Nothing (first task)
**Blocks:** Task 2, Task 3, Task 4

## New Libraries

None.

## Project Structure (Before → After)

```
backend/
  app/
    models/
      ~ todo.py          # Add user_id FK + Relationship
      ~ user.py          # Add back-reference Relationship
  alembic/
    versions/
      645dcb8d91e0_initial.py
      + xxxx_add_todo_user_fk.py   # New migration
```

Legend: `+` added, `~` modified, `-` deleted

## Acceptance Criteria

- [ ] `Todo` model has `user_id: uuid.UUID` field with `foreign_key="user.id"`
- [ ] `user_id` column has a database index
- [ ] `Todo` model has `user: "User"` relationship with `back_populates="todos"`
- [ ] `User` model has `todos: list["Todo"]` relationship with `back_populates="user"`
- [ ] New Alembic migration exists and runs without errors
- [ ] Migration adds the column, FK constraint, and index
- [ ] `uv run alembic upgrade head` succeeds
- [ ] Existing initial migration is untouched

---

## Implementation

### Step 1: Modify `app/models/todo.py`

Add `user_id` foreign key and relationship. Use `TYPE_CHECKING` to avoid circular imports.

```python
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.schemas.mixin import TimeStampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TodoStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class TodoBase(SQLModel):
    title: str = Field(max_length=200, nullable=False)
    description: str = Field(nullable=False)
    status: TodoStatus = Field(default=TodoStatus.NOT_STARTED, nullable=False)
    priority: Priority | None = Field(default=None, nullable=True)
    due_date: datetime | None = Field(default=None, nullable=True)


class Todo(TodoBase, TimeStampMixin, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False
    )
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True, nullable=False)
    user: "User" = Relationship(back_populates="todos")
```

**What changed:**
- Added `from typing import TYPE_CHECKING`
- Added `from sqlmodel import Relationship` (was only `Field, SQLModel`)
- Added `if TYPE_CHECKING` block with `User` import
- Added `user_id` field with FK, index, and not-null
- Added `user` relationship

**Trade-off:** `nullable=False` means you can't create a todo without a user. This is correct — the requirement says "auto-assign to authenticated user."

### Step 2: Modify `app/models/user.py`

Add the back-reference so you can access `user.todos`.

```python
import uuid
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

from app.schemas.mixin import TimeStampMixin

if TYPE_CHECKING:
    from app.models.todo import Todo


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class UserBase(SQLModel):
    email: EmailStr | None = Field(
        default=None, max_length=255, unique=True, index=True, nullable=True
    )
    username: str = Field(max_length=64, unique=True, index=True, nullable=False)
    status: UserStatus = Field(default=UserStatus.ACTIVE, nullable=False)


class User(UserBase, TimeStampMixin, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False
    )
    hashed_password: str = Field(max_length=255, nullable=False)
    todos: list["Todo"] = Relationship(back_populates="user")
```

**What changed:**
- Added `from typing import TYPE_CHECKING`
- Added `Relationship` to sqlmodel import
- Added `if TYPE_CHECKING` block with `Todo` import
- Added `todos` relationship on `User`

### Step 3: Generate Alembic migration

```bash
cd backend
uv run alembic revision --autogenerate -m "add_todo_user_fk"
```

**Expected output:** A new file in `alembic/versions/` with `add_todo_user_fk` in the name.

**Verify the generated migration** contains:
- `op.add_column('todo', sa.Column('user_id', sa.Uuid(), nullable=False))`
- `op.create_foreign_key(...)` referencing `user.id`
- `op.create_index(...)` on `todo.user_id`

### Step 4: Run the migration

```bash
uv run alembic upgrade head
```

**Expected:** No errors. The `todo` table now has a `user_id` column with FK and index.

### Step 5: Verify in database

```bash
docker compose exec db psql -U postgres -d todo_db -c "\d todo"
```

**Expected:** `user_id` column visible with type `uuid`, foreign key to `user.id`, index `ix_todo_user_id`.

### Step 6: Commit

```bash
git add app/models/todo.py app/models/user.py alembic/versions/
git commit -m "feat: add foreign key relationship between Todo and User tables"
```
