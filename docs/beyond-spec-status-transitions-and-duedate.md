# Beyond Spec: Status Transitions & Due Date Editing

Things I noticed while building the assessed submission that could be improved — and how I'd approach them.

## What I Noticed

The backend defines `TodoStatus` with three states — `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED` — but users can never reach `IN_PROGRESS`. The only status control is the toggle endpoint (`/complete`) which jumps between `NOT_STARTED` and `COMPLETED`.

Similarly, `due_date` exists in the backend model and both create/update schemas, but the frontend never exposes it. The field is invisible to users.

## Why This Is a Proposal, Not a Code Change

The spec requires `/todos/{id}/complete` — it's there, it works, and the main branch is complete as assessed. This document captures my thinking on how I'd iterate on it next if given the green light.

## Decisions

### Status transitions — service layer, not Pydantic

Pydantic validates the incoming payload shape. It can't see the current status in the database. So transition rules live in `TodoService.update_todo()`, not in the schema.

### Allowed transitions

```
NOT_STARTED → IN_PROGRESS  ✅  (start working)
NOT_STARTED → COMPLETED    ✅  (skip ahead, quick task)
IN_PROGRESS → NOT_STARTED  ✅  (undo accidental start)
IN_PROGRESS → COMPLETED    ✅  (finish)
COMPLETED   → NOT_STARTED  ✅  (reopen)
COMPLETED   → IN_PROGRESS  ❌  (doesn't make sense — reopen first, then start)
```

Invalid transition returns `400 Bad Request`.

### Remove `/todos/{id}/complete` entirely

No dead endpoints. The PATCH endpoint would handle all status changes with proper validation. Keeping both would be confusing — two ways to change status with different rules.

### Frontend buttons per status

| Status | Actions |
|--------|---------|
| NOT_STARTED | Start, Complete |
| IN_PROGRESS | Un-start, Complete |
| COMPLETED | Uncomplete (→ NOT_STARTED) |

All buttons use `PATCH /todos/{id}` with `{ "status": "TARGET" }`. No new endpoints.

### DateTime picker — send browser timezone, display browser timezone

Backend stores `TIMESTAMPTZ`. Postgres normalizes whatever timezone it receives to UTC internally. So don't over-engineer — send whatever the browser gives, display using the browser's local timezone when reading back. `date-fns` and JS `Date` handle this naturally.

### Due date display — overdue warnings only for incomplete todos

Completed todos show the date in muted text, no warning. Due today shows amber. Past due shows red. No due date shows nothing.

## Trade-offs

| Decision | Upside | Downside |
|----------|--------|----------|
| Remove `/complete` endpoint | Cleaner API, single way to change status | Breaks any client relying on the toggle endpoint |
| Status transitions validated in service layer (not Pydantic/middleware) | Has both request data and DB access — can check current state before allowing transition | Pydantic can't access DB; middleware runs before routing |
| `FutureDatetime` only on create, any datetime on update | Matches backend behavior exactly | Could confuse users — "why can I pick past dates when editing?" |

## Test Coverage

Would include backend tests covering status transition validation (allowed/rejected transitions, 400 on invalid).
