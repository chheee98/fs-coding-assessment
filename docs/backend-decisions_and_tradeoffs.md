# Decisions & Trade-offs

> **Transparency note:** This project was implemented with the assistance of [Claude Code](https://claude.com/claude-code), Anthropic's local AI coding agent. Each decision below was discussed with the AI, where it presented options, trade-offs, and community patterns. The developer (me) made the final call on every decision after understanding the reasoning. This document recaps those decisions from our conversation history.

---

### Architecture

## 1. 3-Tier Architecture (Router → Service → Repository)

**Decision:** Use a layered architecture instead of FastAPI's common flat `crud.py` pattern.

**Why:** Each layer has a single responsibility — router handles HTTP, service handles business logic, repository handles data access. This keeps dependencies flowing in one direction and makes each layer independently testable and reusable.

**Trade-off:** More files and boilerplate compared to tiangolo's flat CRUD template. Acceptable because the separation pays off as the project grows and makes the codebase easier to reason about.

**Reference:** Used by [fastapi_best_architecture](https://github.com/fastapi-practices/fastapi_best_architecture) (2.1k stars) and [FastAPI-Production-Boilerplate](https://github.com/iam-abbas/FastAPI-Production-Boilerplate).

## 2. Schema Base Class — `BaseModel` for DTOs, `SQLModel` for DB Only

**Decision:** Todo schemas (`TodoCreate`, `TodoUpdate`, `TodoRead`, etc.) use Pydantic's `BaseModel` instead of `SQLModel`. `SQLModel` is reserved for DB table models only.

**Why:** Schemas are pure data transfer objects — they never touch the database. Using `SQLModel` for them works (it inherits from `BaseModel`) but is semantically wrong and couples schemas to SQLAlchemy internals they don't need. `BaseModel` makes the intent clear: these are API contracts, not database models.

**Details:**
- Request schemas (`TodoCreate`, `TodoUpdate`) use `BaseModel` with Pydantic's `Field` for validation.
- Response schemas (`TodoRead`, `TodoReadList`) use `BaseModel` with `ConfigDict(from_attributes=True)` so `model_validate(orm_object)` can read ORM attributes.
- Response schemas inherit from `TimeStampReadMixin(BaseModel)` for `created_at`/`updated_at` — separate from the DB model's `TimeStampMixin(SQLModel)` which carries `sa_type` and column config.
- Stats schemas (`TodoPriorityStats`, `TodoStatsRead`) use plain `BaseModel` — no ORM conversion needed.

**Trade-off:** Existing user schemas (`UserRead`, `UserCreate`) still inherit from `UserBase(SQLModel)` because they share field definitions with the DB model. Refactoring those would be a larger change. The todo schemas are the ones I wrote, so I applied the correct pattern there.

## 3. Move `TimeStampMixin` from `schemas/` to `models/`

**Decision:** Move `TimeStampMixin(SQLModel)` from `app/schemas/mixin.py` to `app/models/mixin.py`. Keep `TimeStampReadMixin(BaseModel)` in `app/schemas/mixin.py`.

**Why:** The starter code placed `TimeStampMixin` in `schemas/` — but it has `sa_type=DateTime(timezone=True)` and `sa_column_kwargs`, which are pure SQLAlchemy DB column config. DB models (`Todo`, `User`) were importing from the schema layer, which inverts the dependency direction. Models should never depend on schemas.

**After:**
- `app/models/mixin.py` → `TimeStampMixin(SQLModel)` + `utcnow_aware()` — used by DB models
- `app/schemas/mixin.py` → `TimeStampReadMixin(BaseModel)` — used by response schemas

**Dependency direction:** `schemas/ → models/` (correct). `models/` never imports from `schemas/`.

**Trade-off:** `schemas/user.py` still imports `TimeStampMixin` from `models/` for `UserRead(UserBase, TimeStampMixin)` — this is the pre-existing pattern. The cross-layer dependency is at least in the right direction now (schema depends on model, not the reverse).

## 4. Naming Mismatches Between Layers Are Intentional

**Decision:** Allow different naming across layers (e.g., `toggle_complete` in service vs `complete_todo` in router).

**Discussion:** AI flagged naming inconsistencies in a style review. I pointed out that the layers are independently designed — a repo isn't specific to one service, and a service isn't specific to one route.

**Why:** Each layer names things for its own audience. The router describes the API action. The service describes business logic. The repo describes data operations. A repo's `create()` is generic — it doesn't need to know it's called from a "registration" flow.

---

### Task 1: Database Relationship

## 5. `nullable=False` on `user_id` Foreign Key

**Decision:** Set `user_id` as `nullable=False` (required) on the Todo model.

**Discussion:** Discussed whether to add `default=None` for safety with existing data. Since the database starts empty for this assessment, the constraint is safe.

**Why:** Every todo must belong to an authenticated user. Allowing orphan todos doesn't match the business requirements.

**Trade-off:** For an existing production DB with NULL `user_id` rows, you'd need to backfill first, then enforce the constraint.

---

### Task 2: CRUD Endpoints

## 6. Repository Accepts DB Model, Not Schema

**Decision:** `TodoRepository.create(todo: Todo)` receives a DB model. The service handles schema-to-model conversion.

**Discussion:** AI presented two options — (A) repo accepts DB model, (B) repo accepts Pydantic schema (like the existing `UserRepository` does). After comparing dependency direction, reusability, and where business logic belongs, I chose Option A.

**Why:** The repository is a pure persistence layer — it should not depend on API schemas. This keeps the dependency direction clean (repo never imports from `schemas/`) and makes the repo reusable from any context (services, background jobs, CLI scripts, tests) without requiring callers to construct Pydantic schemas just to persist data.

**Trade-off:** The service has slightly more code to build the model before calling the repo. Worth it for proper separation of concerns. The existing `UserRepository` uses the opposite pattern (accepts schema) — I'd refactor it to match given more time.

## 7. Static Routes Before Path Parameters (Route Ordering)

**Decision:** Define `GET /todos/stats` before `GET /todos/{todo_id}` in the router.

**Discussion:** Stats tests were returning 422 (Unprocessable Entity) instead of 200. Investigation revealed FastAPI was matching `/stats` against the `/{todo_id}` route first, trying to parse `"stats"` as a UUID — which fails validation.

**Why:** FastAPI matches routes in definition order. A path parameter like `/{todo_id}` is greedy — it captures any path segment, including literal strings like `stats`. Static segments must be registered first so they match before the parameter route is evaluated.

**Trade-off:** Route definition order becomes load-bearing — reordering routes can silently break the API. This is a well-known FastAPI behavior documented in [Path Operation Order](https://fastapi.tiangolo.com/tutorial/path-params/#order-matters).

## 8. Description Hiding in Python, Not SQL

**Decision:** The `GET /todos` list endpoint hides descriptions of non-owner todos at the service layer (Python), not via SQL query.

**Why:** Far more readable and testable. The service iterates over results and nulls out `description` for non-owner todos.

**Trade-off:** All descriptions are fetched from the DB even when nulled out. For a todo app's data volume, this is negligible.

## 9. `due_date` Validation Only on Create, Not Update

**Decision:** `TodoCreate` validates that `due_date` must be in the future via `@field_validator`. `TodoUpdate` has no such validation.

**Why:** When creating a todo, a past due date makes no sense. But when updating an old todo (e.g., changing just the title), the existing `due_date` may already be in the past — rejecting the update because of an unrelated field is a bad user experience.

**Trade-off:** A user could explicitly update `due_date` to a past date. Accepted because the alternative (blocking all updates on overdue todos) is worse.

## 10. Bearer Token Auth (Not HttpOnly Cookies)

**Decision:** Keep the existing Bearer token + localStorage approach for JWT auth.

**Discussion:** I questioned why the assessment mentions XSS protection while using Bearer tokens in localStorage (which is inherently XSS-vulnerable). After discussion, the conclusion was: the assessment expects Bearer tokens (existing auth code uses it) + XSS prevention at the code level (input validation, no raw HTML rendering, security headers). These are separate concerns.

**Trade-off:** localStorage is vulnerable to XSS — if an XSS attack succeeds, the token can be stolen. In production, HttpOnly cookies would be the better choice. For this assessment, the existing auth architecture was kept as-is.

---

### Task 3: Statistics Endpoint

## 11. `session.execute()` for Aggregate Queries

**Decision:** Use SQLAlchemy's `session.execute()` instead of SQLModel's `session.exec()` for raw aggregate queries (stats, counts).

**Why:** `session.exec()` is SQLModel's wrapper that auto-unwraps ORM model objects. For aggregate queries like `select(func.count().label("total"))`, there are no model objects to unwrap — `execute()` is the correct tool.

**Trade-off:** The IDE warns about using `execute()` instead of `exec()`. These warnings can be safely ignored for non-model queries.

## 12. Two Separate Stats Queries (Overall + Priority)

**Decision:** Split statistics into two repository methods — `get_overall_statistics()` and `get_statistics_by_priority()` — instead of one combined query.

**Discussion:** The plan originally had one fat repo method that did both queries, looped, and built the response dict. I split it into two focused methods and moved the assembly to the service layer.

**Why:** Each method does one query and returns raw data. The service assembles the final response. This keeps the repo methods focused and reusable.

**Trade-off:** Two DB round-trips instead of one. For per-user stats on a todo app, the data volume is tiny and the simplicity is worth it.

---

### Task 4: Tests

## 13. Test DB Strategy — Separate `.env.test`, No Docker Dependency

**Decision:** Tests use an independent `TEST_DATABASE_URL` from `.env.test`, completely decoupled from the main app's `.env`. No Docker scripts or init scripts involved — just `uv run pytest`.

**Why:** Tests should run with a single command. Coupling test config to the main app risks accidentally running tests against the real database. A separate `.env.test` makes the boundary explicit.

**Trade-off:** Developer must manually create the test database and configure `.env.test`. A `.env.test.example` is provided as a template.

## 14. `NullPool` for Test Engine

**Decision:** Use `NullPool` on the test async engine instead of the default connection pool.

**Discussion:** Tests were failing with `InterfaceError: another operation is in progress` — asyncpg doesn't allow concurrent operations on the same connection. The default pool reuses connections, so overlapping async requests (e.g., register + login in a fixture) would grab the same connection.

**Why:** `NullPool` creates a fresh connection per session and disposes it after use. No reuse = no concurrency conflicts.

**Trade-off:** No pooling means slightly slower connections — but that's the wrong concern here. Pytest tests verify **correctness** (right data? right status code?), not pool behavior. Pool-related issues (exhaustion, concurrency under load) belong to load testing with tools like `locust` or `k6` against a real running server. Different test layers, different tools — `NullPool` is the right call for this layer.

## 15. Test Fixtures — `auth_user` Bundles Identity with Auth

**Decision:** The `auth_user` fixture registers a user and returns both auth headers and user info (`{"headers": {...}, "user": {...}}`).

**Why:** Tests often need to verify ownership — e.g., asserting `response["user_id"]` matches the logged-in user. The register endpoint already returns `UserRead` (with `id`, `username`, `email`), so the fixture captures it alongside the token. One fixture call gives tests everything they need — no extra API requests to look up "who am I?"

**Trade-off:** Headers are accessed via `auth_user["headers"]` instead of being a flat dict. Slightly more verbose, but tests gain full user context for free.

## 16. Test Lifecycle — Class-Scoped Table Setup

**Decision:** Split DB setup into two fixtures: `verify_db` (`scope="session"`) checks the connection once, `setup_database` (`scope="class"`) creates and drops all tables per test class.

**Discussion:** With session scope, all test classes shared DB state. This caused issues — e.g., `test_get_empty_list` couldn't guarantee an empty list because earlier classes had already created todos. Filtering by `user_id` was a workaround, but class-scoped cleanup is cleaner.

**Why:** Each test class starts with a clean database. No leftover data from other classes. Tests within the same class still share state (which is fine — they're testing the same endpoint group).

**Trade-off:** Slightly slower — tables are created/dropped per class (~10 cycles) instead of once. For a small test suite this is negligible. `pytest.exit()` is still used in `verify_db` for clean error messages on connection failure.

## 17. Test Structure — 3A Pattern, Organized by Endpoint

**Decision:** Tests follow the Arrange-Act-Assert pattern, grouped into classes by endpoint (`TestCreateTodo`, `TestGetTodos`, `TestUpdateTodo`, etc.) with a separate `TestTodoLifecycle` for chained operations.

**Why:** Class grouping makes it easy to run a subset (`pytest ::TestCreateTodo`). The lifecycle test catches DB state bugs that isolated endpoint tests miss — e.g., create → update → toggle → verify stats → delete → verify gone.

---

### Reusable Patterns

## 18. BaseRepository with `_paginate` Helper

**Decision:** Extract a `BaseRepository` class with a shared `_paginate()` method that all repositories inherit from.

**Discussion:** Initially `_paginate` was a private method inside `TodoRepository`. I questioned how it was "reusable" if it was stuck in one class — that led to extracting it into a base class.

**Why:** Pagination (count query + offset/limit) is identical across any paginated list endpoint. `TodoRepository` inherits `_paginate` for free, and any future repository (users, comments) gets it too.

**Trade-off:** Adds an inheritance layer. Technically violates ISP (Interface Segregation Principle) — not every repository needs pagination, yet all inheritors get `_paginate`. A stricter SOLID approach would use a separate `ListableRepository` mixin. Accepted here because `_paginate` is a single lightweight helper, not a bloated interface — the pragmatic benefit outweighs the purity cost. The `BaseRepository` pattern is less common in Python/FastAPI than in .NET Core, but fits naturally when you already have a 3-tier architecture.

## 19. Generic `PaginatedResponse[T]` Schema

**Decision:** Use a generic `PaginatedResponse[T]` base schema (`BaseModel + Generic[T]`) instead of a hardcoded `TodoPaginatedResponse`.

**Discussion:** I wanted a reusable pagination wrapper for future entities. AI researched community patterns — `BaseModel + Generic[T]` is the standard approach, confirmed by `fastapi-pagination` library internals and Pydantic v2 docs.

**Why:** The pagination wrapper (`items`, `total`, `page`, `page_size`, `total_pages`) is the same for any entity. Includes a `create()` class method that auto-calculates `total_pages` so services don't repeat the math.

**Trade-off:** Generics add slight complexity. Pydantic v2 handles them well and auto-generates correct OpenAPI schemas. Used `BaseModel` instead of `SQLModel` because this is a pure response wrapper with no DB involvement.
