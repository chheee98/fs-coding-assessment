# Backend Assessment - FastAPI Todo API with Authentication & Database

## Overview

This assessment evaluates your ability to build a **production-grade RESTful API** using FastAPI. You'll create a secure, scalable backend for a todo management system with authentication, database integration, and comprehensive testing.

**Key Focus Areas**:

- Database design and migrations (SQLModel/Alembic)
- Advanced API patterns (pagination, filtering, searching)
- Input validation and error handling
- Testing and code quality
- Security best practices

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- PostgreSQL running locally (or via Docker)

### Setup

1. Clone this repository

2. Install dependencies:
   ```bash
   cd backend
   uv sync
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   cp .env.test.example .env.test
   ```
   Edit `.env` and `.env.test` to match your local PostgreSQL connection (host, port, username, password).

4. Run database migrations:
   ```bash
   uv run alembic upgrade head
   ```

5. Run the development server:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

6. Run tests:
   ```bash
   uv run pytest                                                    # all tests
   uv run pytest tests/test_todos.py -v                             # todo tests only
   uv run pytest tests/test_todos.py::TestRequiredByAssessment -v   # assessment-required only
   ```

> Tests use a separate database (`TEST_DATABASE_URL` in `.env.test`), completely independent from the main app.

The API will be available at `http://localhost:8000` — interactive docs at `http://localhost:8000/docs`

## Required Tasks

### Task 1: Database Relationship - Connect Todo and User Tables

### Task 2: Implement Todo CRUD API Endpoints

Implement complete CRUD operations for todos. All endpoints require authentication (Bearer token).

#### POST /api/v1/todos

Create a new todo:

- Accept: `title`, `description`, `priority` (optional), `due_date` (optional)
- Auto-assign to authenticated user
- Return created todo with 201 status

#### GET /api/v1/todos

Get all todos:

- Return all todos from ALL users (authenticated users can see others' todos)
- Hide `description` field for todos not owned by the current user
- Query pagination (default page=1 & page_size=20)
- Query filtering by priority/completed
- Search title functionality
- Include `user_id` or `User` to identify owner

#### GET /api/v1/todos/{todo_id}

Get single todo:

- Only owner can access full details
- Return 403 if user tries to access someone else's todo
- Return 404 if todo doesn't exist

#### PUT /api/v1/todos/{todo_id} or PATCH /api/v1/todos/{todo_id}

Update todo:

- Only owner can update
- Support partial updates (PATCH)
- Validate input fields
- Return 403 if not owner

#### DELETE /api/v1/todos/{todo_id}

Delete todo:

- Only owner can delete
- Return 204 on success
- Return 403 if not owner

#### PATCH /api/v1/todos/{todo_id}/complete

Mark todo as complete:

- Only owner can mark as complete
- Toggle `completed` status
- Return updated todo

### Task 3: Implement Todo Statistics Endpoint

#### GET /api/v1/todos/stats

Get statistics for the authenticated user's todos:

**Response format**:

```json
{
  "total": 10,
  "completed": 4,
  "pending": 6,
  "by_priority": {
    "LOW": 3,
    "MEDIUM": 5,
    "HIGH": 2
  }
}
```

**Requirements**:

- Only count todos belonging to the authenticated user
- Calculate totals efficiently (use database aggregation if possible)
- Return proper schema with type validation

### Task 4: Write Test Cases

**Priority: CRITICAL**

Create test file `tests/test_todos.py` with the following test cases:

**Required Tests**:

1. **`test_create_todo_success`** - Create todo successfully
   - Test that an authenticated user can create a todo
   - Verify the response contains correct data
   - Verify status code is 201

2. **`test_get_all_todos`** - Get all todos
   - Test that an authenticated user can get all todos
   - Verify description is hidden for todos not owned by the user
   - Verify todos show user_id or username to identify owner
   - Verify status code is 200

Run tests:

```bash
uv run pytest tests/test_todos.py -v
```

## Checklist

### Core Requirements (Must Complete)

- [ ] **Task 1**: Add foreign key relationship between Todo and User tables
- [ ] **Task 2**: Implement all 6 Todo CRUD endpoints
  - [ ] POST /api/v1/todos (Create)
  - [ ] GET /api/v1/todos (List all - hide description for non-owners, pagination, filtering, search)
  - [ ] GET /api/v1/todos/{id} (Get single - owner only)
  - [ ] PATCH /api/v1/todos/{id} (Update - owner only)
  - [ ] DELETE /api/v1/todos/{id} (Delete - owner only)
  - [ ] PATCH /api/v1/todos/{id}/complete (Mark complete - owner only)
- [ ] **Task 3**: Implement GET /api/v1/todos/stats endpoint
- [ ] **Task 4**: Write tests in `tests/test_todos.py`
  - [ ] test_create_todo_success
  - [ ] test_get_all_todos (verify description hiding for non-owners)

### Code Quality

- [ ] Type hints on all functions
- [ ] Proper error handling with custom exceptions
- [ ] Docstrings on all endpoints
- [ ] Follow RESTful conventions
- [ ] Use proper HTTP status codes
- [ ] Input validation with Pydantic

### Database

- [ ] Foreign key constraint added with migration
- [ ] Database indexes on `user_id`
- [ ] Proper async database sessions

## Submission

Ensure your submission:
Testing Your Implementation

### Run the Application

```bash
uv run uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` to test endpoints interactively.

### Run Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run only todo tests
uv run pytest tests/test_todos.py -v

# Run with coverage
uv run pytest tests/test_todos.py -v --cov=app --cov-report=html --cov-report=term
```

### Test the Endpoints Manually

1. **Register a user**:

   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","username":"testuser","password":"Password123!"}'
   ```

2. **Login and get token**:

   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"Password123!"}'
   ```

3. **Create a todo** (use token from login):

   ```bash
   curl -X POST http://localhost:8000/api/v1/todos \
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Content-Type: application/json" \
     -d '{"title":"Test Todo","description":"Test description","priority":"HIGH"}'
   ```

4. **Get all todos**:

   ```bash
   curl -X GET http://localhost:8000/api/v1/todos \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
   ```

5. **Get stats**:
   ```bash
   curl -X GET http://localhost:8000/api/v1/todos/stats \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
   ```

## Submission Checklist

Before submitting, ensure:

- [ ] All 4 core tasks are completed
- [ ] Application starts without errors
- [ ] All tests pass (`uv run pytest tests/ -v`)
- [ ] Test coverage is at least 70% for todo endpoints
- [ ] API documentation at `/docs` shows all endpoints
- [ ] Foreign key relationship exists between Todo and User
- [ ] Both required test cases are implemented and passingtodos
- [ ] Stats endpoint returns correct calculations
- [ ] Code follows Python best practices (type hints, docstrings)
