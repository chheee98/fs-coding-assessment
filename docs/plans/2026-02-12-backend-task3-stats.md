# Backend Task 3: Todo Statistics Endpoint

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement `GET /api/v1/todos/stats` that returns completion and priority breakdown for the authenticated user's todos.

**Architecture:** Add a stats schema, a stats query in the repository (database aggregation), a service method, and wire up the existing router placeholder from Task 2.

**Tech Stack:** FastAPI, SQLModel, SQLAlchemy `func.count` + `case`, PostgreSQL

---

## Quick Context

The stats endpoint returns how many todos the current user has, how many are completed/pending, and a breakdown by priority. The requirement specifies an exact JSON response shape. The router placeholder already exists from Task 2 — this task replaces it with the real implementation.

**Depends on:** Task 1 (user_id FK), Task 2 (repository/service patterns)
**Blocks:** Task 4 (tests may validate stats indirectly)

## New Libraries

None.

## Project Structure (Before → After)

```
backend/
  app/
    schemas/
      ~ todo.py                  # Add TodoStats schema
    repositories/
      ~ todo_repository.py       # Add get_stats method
    services/
      ~ todo_service.py          # Add get_stats method
    routers/
      ~ todos.py                 # Replace stats placeholder
```

## Acceptance Criteria

- [ ] `GET /api/v1/todos/stats` returns correct JSON shape:
  ```json
  {
    "total": 10,
    "completed": 4,
    "pending": 6,
    "by_priority": { "LOW": 3, "MEDIUM": 5, "HIGH": 2 }
  }
  ```
- [ ] Only counts todos belonging to the authenticated user
- [ ] Uses database aggregation (not Python-side counting)
- [ ] Returns zeros when user has no todos
- [ ] `by_priority` includes all three keys even if count is 0
- [ ] Requires Bearer token authentication

---

## Implementation

### Step 1: Add `TodoStats` schema to `app/schemas/todo.py`

Append this to the existing schemas file:

```python
class TodoPriorityStats(SQLModel):
    """Priority breakdown for stats."""

    LOW: int = 0
    MEDIUM: int = 0
    HIGH: int = 0


class TodoStats(SQLModel):
    """Response schema for todo statistics."""

    total: int = 0
    completed: int = 0
    pending: int = 0
    by_priority: TodoPriorityStats = TodoPriorityStats()
```

**Explanation:** Default values of `0` ensure the response is valid even when a user has no todos. `TodoPriorityStats` is a nested model so the JSON shape matches the requirement exactly.

### Step 2: Add `get_stats` method to `app/repositories/todo_repository.py`

Append this method to the `TodoRepository` class:

```python
    async def get_stats(self, user_id: uuid.UUID) -> dict:
        """Get todo statistics for a specific user using database aggregation."""
        # Total and completed/pending counts
        statement = select(
            func.count().label("total"),
            func.count().filter(Todo.status == TodoStatus.COMPLETED).label("completed"),
            func.count().filter(Todo.status != TodoStatus.COMPLETED).label("pending"),
        ).where(Todo.user_id == user_id)

        result = await self.session.exec(statement)
        row = result.one()

        # Priority breakdown
        priority_statement = select(
            Todo.priority,
            func.count().label("count"),
        ).where(
            Todo.user_id == user_id,
            Todo.priority.is_not(None),
        ).group_by(Todo.priority)

        priority_result = await self.session.exec(priority_statement)
        priority_rows = priority_result.all()

        by_priority = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        for priority_row in priority_rows:
            by_priority[priority_row.priority.value] = priority_row.count

        return {
            "total": row.total,
            "completed": row.completed,
            "pending": row.pending,
            "by_priority": by_priority,
        }
```

**Note:** You also need to add this import at the top of the file if not already present:

```python
from app.models.todo import Priority, Todo, TodoStatus
```

**Explanation:** Two queries — one for totals, one for priority breakdown. Uses `func.count().filter()` for conditional counting (PostgreSQL `FILTER (WHERE ...)` syntax via SQLAlchemy).

**Trade-off:** Two queries instead of one complex query. Simpler to read, and for per-user stats the data volume is tiny. A single query with `case()` expressions would also work but is harder to maintain.

### Step 3: Add `get_stats` method to `app/services/todo_service.py`

Append this method to the `TodoService` class. Add the import for `TodoStats` and `TodoPriorityStats`:

Add to imports at top:

```python
from app.schemas.todo import (
    TodoCreate,
    TodoPaginatedResponse,
    TodoPriorityStats,
    TodoRead,
    TodoReadList,
    TodoStats,
    TodoUpdate,
)
```

Add method to class:

```python
    async def get_stats(self, user_id: uuid.UUID) -> TodoStats:
        """Get todo statistics for the authenticated user."""
        stats_data = await self.todo_repository.get_stats(user_id)
        return TodoStats(
            total=stats_data["total"],
            completed=stats_data["completed"],
            pending=stats_data["pending"],
            by_priority=TodoPriorityStats(**stats_data["by_priority"]),
        )
```

### Step 4: Replace stats placeholder in `app/routers/todos.py`

Replace the existing `get_stats` function. Add `TodoStats` to the import:

```python
from app.schemas.todo import (
    TodoCreate,
    TodoPaginatedResponse,
    TodoRead,
    TodoStats,
    TodoUpdate,
)
```

Replace the function:

```python
@router.get("/stats", response_model=TodoStats)
async def get_stats(
    todo_service: TodoServiceDep,
    current_user: CurrentUserDep,
) -> TodoStats:
    """Get statistics for the authenticated user's todos."""
    return await todo_service.get_stats(current_user.id)
```

### Step 5: Verify manually

```bash
# With the server running and a Bearer token:
curl -X GET http://localhost:8000/api/v1/todos/stats \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected response (for a user with some todos):**

```json
{
  "total": 3,
  "completed": 1,
  "pending": 2,
  "by_priority": {
    "LOW": 1,
    "MEDIUM": 1,
    "HIGH": 1
  }
}
```

**Expected response (for a user with no todos):**

```json
{
  "total": 0,
  "completed": 0,
  "pending": 0,
  "by_priority": {
    "LOW": 0,
    "MEDIUM": 0,
    "HIGH": 0
  }
}
```

### Step 6: Commit

```bash
git add app/schemas/todo.py app/repositories/todo_repository.py app/services/todo_service.py app/routers/todos.py
git commit -m "feat: implement todo statistics endpoint with priority breakdown"
```
