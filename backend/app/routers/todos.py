import uuid

from fastapi import APIRouter, Query, status
from app.dependencies.auth import CurrentUserDep
from app.dependencies.todo import TodoServiceDep
from app.models.todo import Priority
from app.schemas.todo import TodoCreate, TodoPaginatedResponse, TodoRead, TodoUpdate

router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_todo(
    todo_in: TodoCreate,
    todo_service: TodoServiceDep,
    current_service: CurrentUserDep,
):
    """Create a new todo for the authenticated user."""
    return await todo_service.create_todo(todo_in, current_service.id)


@router.get("")
async def get_todos(
    todo_service: TodoServiceDep,
    current_user: CurrentUserDep,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    priority: Priority | None = Query(default=None, description="Filter by priority"),
    completed: bool | None = Query(
        default=None, description="Filter by completed status"
    ),
    search: str | None = Query(
        default=None, min_length=1, description="Search by title"
    ),
) -> TodoPaginatedResponse:
    """Get all todos with pagination, filtering, and search. Hides description for non-owner todos."""
    return await todo_service.get_todos(
        current_user_id=current_user.id,
        page=page,
        page_size=page_size,
        priority=priority,
        completed=completed,
        search=search,
    )


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
    """Toggle todo completion status. Only the owner can toggle."""
    return await todo_service.toggle_complete(todo_id, current_user.id)


@router.get("/stats")
async def get_stats(
    todo_service: TodoServiceDep,
    current_user: CurrentUserDep,
):
    """Get todo statistics for the authenticated user."""
    return await todo_service.get_statistics(current_user.id)
