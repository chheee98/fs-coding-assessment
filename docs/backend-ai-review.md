# AI Code Review Process

## Why a Separate Review Step?

After implementing all backend tasks and passing all test cases with manual verification, I added an AI review step before submitting. The reasoning is simple: **I'm human, and I miss things.**

Tests prove the code works. Manual verification confirms the happy path. But subtle issues — timezone edge cases, schema-DB mismatches, missing type annotations, security hygiene — are easy to overlook when you're deep in implementation. An external reviewer catches what familiarity blinds you to.

## Why Codex Over Claude Code?

I used both AI tools throughout this project — **Claude Code** for brainstorming, planning, and implementation assistance, and **OpenAI Codex** for post-implementation review.

Codex turned out to be more effective as a reviewer because it respects the current codebase structure when analyzing. Rather than suggesting rewrites, it pointed to specific lines and explained exactly what could go wrong at runtime. That precision matters when reviewing — you want "line 19 will crash with TypeError when given a timezone-aware datetime" not "consider refactoring your validation approach."

## When Does Review Happen?

The review runs **after** all of this is done:

1. All planned tasks are implemented
2. All test cases pass (`uv run pytest`)
3. Manual verification through `/docs` (Swagger UI) confirms endpoints work
4. Code is committed and working

Only then do I run the review. It's not part of the development loop — it's a final quality gate.

## What Happens When Review Finds Issues?

Findings go back through the same workflow:

```
Review finding → Brainstorm fix → Implement → Test → Verify → Re-review
```

This iterates until the review comes back clean. Examples from this project:

| Finding | Severity | Fix |
|---|---|---|
| `due_date` validation crashes on timezone-aware datetimes (`...Z`) | High | Replaced custom validator with Pydantic's built-in `FutureDatetime` |
| PATCH accepts `null` for DB non-nullable fields → 500 IntegrityError | High | Added `@field_validator` to reject explicit null on `description` and `status` |
| Stats schema has extra `failed` field not in assessment spec | Medium | Removed the field |
| Missing `response_model` and return annotations on 2 endpoints | Medium | Added `response_model=` and `-> ReturnType` |
| `print(token_data)` leaks JWT payload to stdout | Low | Removed (was in template code — caught it anyway) |
| Invalid token returns 403 instead of 401 | Low | Changed to `HTTP_401_UNAUTHORIZED` (was in template code) |

Each fix was tested, verified, and re-reviewed before moving on.

## In a Real Project

In a real project, this review step would happen **before creating a PR**. The loop would be:

```
Implement → Test → Verify → AI Review → Fix findings → Re-review → PR
```

For this assessment, "submit" replaces "PR," but the discipline is the same — don't ship what hasn't been reviewed.