# CLAUDE.md

## Question Rewriting

When I ask a question in rough or unclear phrasing, **rewrite my question first** before answering. Show the rewritten version so I can see how you understood it. This helps me learn to write better prompts.

Format:
> **Your question, rephrased:** [clearer version of what I asked]

Then answer the rephrased question.

### Examples
| What I typed | Rephrased |
|---|---|
| the main question is here backend/app, so manny folder, what kind of code should I place into what result? | In a `backend/app` with many folders, what kind of code should go where? |
| this test not work how to fix? | This test is failing — how do I debug and fix it? |
| why this error when I run server? | I'm getting an error when I start the dev server. What's causing it and how do I fix it? |
| how to make frontend talk to backend? | How do I connect the Next.js frontend to the FastAPI backend API? |

## Vibecoding Approach

This project follows a structured vibecoding workflow:

1. **Brainstorm** — Explore intent, requirements, and design before writing any code.
2. **Planning** — Each task has its own plan file under `docs/plans/`. Every plan file follows this structure:
   - **Quick Context** — What this task is, why it matters, dependencies on other tasks
   - **New Libraries** — Any new dependencies needed (or "None")
   - **Project Structure (Before → After)** — Highlight files changed (`~`), added (`+`), deleted (`-`)
   - **Acceptance Criteria** — Checklist of what "done" looks like
   - **Implementation** — Code snippets with explanation, trade-offs, and rationale
3. **Developer picks & implements** — The developer selects code from the plan and applies it manually. If anything is uncertain or doesn't feel right, go back to step 2 and revise the plan to ensure it follows community standards and best practices.
4. **Manual verify/testing** — Verify the implementation works correctly through manual testing.

Key principle: The developer is always in control. AI assists with brainstorming and planning, but the developer makes the final call on what code goes in. When in doubt, revise the plan rather than pushing through with uncertainty.

## Project: Full Stack TODO Application (Coding Assessment)

Source: https://github.com/topschool-ai/fs-coding-assessment

### Tech Stack
- **Backend**: FastAPI + PostgreSQL + SQLModel + Alembic + JWT auth (Python 3.12+, uv)
- **Frontend**: Next.js (App Router) + TypeScript + Tailwind CSS + Context API

### Backend Tasks (each has a plan file in `docs/plans/`)
1. `docs/plans/2026-02-12-backend-task1-db-relationship.md` — Foreign key Todo ↔ User
2. `docs/plans/2026-02-12-backend-task2-todo-crud.md` — 6 CRUD endpoints + schemas + repository + service + dependency
3. `docs/plans/2026-02-12-backend-task3-stats.md` — GET /api/v1/todos/stats
4. `docs/plans/2026-02-12-backend-task4-tests.md` — test_create_todo_success, test_get_all_todos

### Frontend Tasks
1. Authentication system (login, register, JWT, protected routes)
2. Todo management (list, CRUD, filtering, search, pagination)
3. Optimistic updates & error handling
4. Accessibility & UX (semantic HTML, ARIA, keyboard nav)
5. Responsive design with Tailwind CSS

### Evaluation Criteria
- Code Quality (30%) — clean, typed, documented
- Functionality (25%) — all features working
- Architecture (20%) — proper separation of concerns
- Testing (15%) — comprehensive coverage
- Security (10%) — auth, validation, secure practices

### Workflow Order
1. Backend first (frontend depends on API)
2. Frontend after API is verified working
3. Tests alongside each backend task
4. Manual verification at each step via `/docs` and browser