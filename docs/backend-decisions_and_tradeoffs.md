# Architecture Decisions & Trade-offs

> **Transparency note:** This project was implemented with the assistance of [Claude Code](https://claude.com/claude-code), Anthropic's local AI coding agent. Each decision below was discussed with the AI, where it presented options, trade-offs, and community patterns. The developer (me) made the final call on every decision after understanding the reasoning. This document recaps those decisions from our conversation history.

---

## 1. 3-Tier Architecture (Router → Service → Repository)

**Decision:** Use a layered architecture instead of FastAPI's common flat `crud.py` pattern.

**Why:** Each layer has a single responsibility — router handles HTTP, service handles business logic, repository handles data access. This keeps dependencies flowing in one direction and makes each layer independently testable and reusable.

**Trade-off:** More files and boilerplate compared to tiangolo's flat CRUD template. Acceptable because the separation pays off as the project grows and makes the codebase easier to reason about.

**Reference:** Used by [fastapi_best_architecture](https://github.com/fastapi-practices/fastapi_best_architecture) (2.1k stars) and [FastAPI-Production-Boilerplate](https://github.com/iam-abbas/FastAPI-Production-Boilerplate).

## 2. Repository Accepts DB Model, Not Schema (Option A)

**Decision:** `TodoRepository.create(todo: Todo)` receives a DB model. The service handles schema-to-model conversion.

**Discussion:** AI presented two options — (A) repo accepts DB model, (B) repo accepts Pydantic schema (like the existing `UserRepository` does). After comparing dependency direction, reusability, and where business logic belongs, I chose Option A.

**Why:** The repository is a pure persistence layer — it should not depend on API schemas. This keeps the dependency direction clean (repo never imports from `schemas/`) and makes the repo reusable from any context (services, background jobs, CLI scripts, tests) without requiring callers to construct Pydantic schemas just to persist data.

**Trade-off:** The service has slightly more code to build the model before calling the repo. Worth it for proper separation of concerns. The existing `UserRepository` uses the opposite pattern (accepts schema) — I'd refactor it to match given more time.

## 3. BaseRepository with `_paginate` Helper

**Decision:** Extract a `BaseRepository` class with a shared `_paginate()` method that all repositories inherit from.

**Discussion:** Initially `_paginate` was a private method inside `TodoRepository`. I questioned how it was "reusable" if it was stuck in one class — that led to extracting it into a base class.

**Why:** Pagination (count query + offset/limit) is identical across any paginated list endpoint. `TodoRepository` inherits `_paginate` for free, and any future repository (users, comments) gets it too.

**Trade-off:** Adds an inheritance layer. Technically violates ISP (Interface Segregation Principle) — not every repository needs pagination, yet all inheritors get `_paginate`. A stricter SOLID approach would use a separate `ListableRepository` mixin. Accepted here because `_paginate` is a single lightweight helper, not a bloated interface — the pragmatic benefit outweighs the purity cost. The `BaseRepository` pattern is less common in Python/FastAPI than in .NET Core, but fits naturally when you already have a 3-tier architecture.

## 4. Generic `PaginatedResponse[T]` Schema

**Decision:** Use a generic `PaginatedResponse[T]` base schema (`BaseModel + Generic[T]`) instead of a hardcoded `TodoPaginatedResponse`.

**Discussion:** I wanted a reusable pagination wrapper for future entities. AI researched community patterns — `BaseModel + Generic[T]` is the standard approach, confirmed by `fastapi-pagination` library internals and Pydantic v2 docs.

**Why:** The pagination wrapper (`items`, `total`, `page`, `page_size`, `total_pages`) is the same for any entity. Includes a `create()` class method that auto-calculates `total_pages` so services don't repeat the math.

**Trade-off:** Generics add slight complexity. Pydantic v2 handles them well and auto-generates correct OpenAPI schemas. Used `BaseModel` instead of `SQLModel` because this is a pure response wrapper with no DB involvement.

## 5. Bearer Token Auth (Not HttpOnly Cookies)

**Decision:** Keep the existing Bearer token + localStorage approach for JWT auth.

**Discussion:** I questioned why the assessment mentions XSS protection while using Bearer tokens in localStorage (which is inherently XSS-vulnerable). After discussion, the conclusion was: the assessment expects Bearer tokens (existing auth code uses it) + XSS prevention at the code level (input validation, no raw HTML rendering, security headers). These are separate concerns.

**Trade-off:** localStorage is vulnerable to XSS — if an XSS attack succeeds, the token can be stolen. In production, HttpOnly cookies would be the better choice. For this assessment, the existing auth architecture was kept as-is.

## 6. `session.execute()` for Aggregate Queries

**Decision:** Use SQLAlchemy's `session.execute()` instead of SQLModel's `session.exec()` for raw aggregate queries (stats, counts).

**Why:** `session.exec()` is SQLModel's wrapper that auto-unwraps ORM model objects. For aggregate queries like `select(func.count().label("total"))`, there are no model objects to unwrap — `execute()` is the correct tool.

**Trade-off:** The IDE warns about using `execute()` instead of `exec()`. These warnings can be safely ignored for non-model queries.

## 7. Two Separate Stats Queries (Overall + Priority)

**Decision:** Split statistics into two repository methods — `get_overall_statistics()` and `get_statistics_by_priority()` — instead of one combined query.

**Discussion:** The plan originally had one fat repo method that did both queries, looped, and built the response dict. I split it into two focused methods and moved the assembly to the service layer.

**Why:** Each method does one query and returns raw data. The service assembles the final response. This keeps the repo methods focused and reusable.

**Trade-off:** Two DB round-trips instead of one. For per-user stats on a todo app, the data volume is tiny and the simplicity is worth it.

## 8. Description Hiding in Python, Not SQL

**Decision:** The `GET /todos` list endpoint hides descriptions of non-owner todos at the service layer (Python), not via SQL query.

**Why:** Far more readable and testable. The service iterates over results and nulls out `description` for non-owner todos.

**Trade-off:** All descriptions are fetched from the DB even when nulled out. For a todo app's data volume, this is negligible.

## 9. Naming Mismatches Between Layers Are Intentional

**Decision:** Allow different naming across layers (e.g., `toggle_complete` in service vs `complete_todo` in router).

**Discussion:** AI flagged naming inconsistencies in a style review. I pointed out that the layers are independently designed — a repo isn't specific to one service, and a service isn't specific to one route.

**Why:** Each layer names things for its own audience. The router describes the API action. The service describes business logic. The repo describes data operations. A repo's `create()` is generic — it doesn't need to know it's called from a "registration" flow.

## 10. `nullable=False` on `user_id` Foreign Key

**Decision:** Set `user_id` as `nullable=False` (required) on the Todo model.

**Discussion:** Discussed whether to add `default=None` for safety with existing data. Since the database starts empty for this assessment, the constraint is safe.

**Why:** Every todo must belong to an authenticated user. Allowing orphan todos doesn't match the business requirements.

**Trade-off:** For an existing production DB with NULL `user_id` rows, you'd need to backfill first, then enforce the constraint.