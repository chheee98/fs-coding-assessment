import uuid

from app.exceptions.http import NotFoundException, ForbiddenException
from app.models.todo import Todo, Priority, TodoStatus
from app.repositories.todo_repository import TodoRepository
from app.schemas.todo import (
    TodoCreate,
    TodoRead,
    TodoPaginatedResponse,
    TodoReadList,
    TodoUpdate,
    TodoStatsRead,
)


class TodoService:
    def __init__(self, todo_repository: TodoRepository):
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

        return TodoPaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_todo(
        self, todo_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> TodoRead:
        """Get a single todo. Only the owner can access."""
        todo = await self._get_todo_or_404(todo_id)
        self._check_owner(todo, current_user_id)
        return TodoRead.model_validate(todo)

    async def update_todo(
        self,
        todo_id: uuid.UUID,
        todo_in: TodoUpdate,
        current_user_id: uuid.UUID,
    ) -> TodoRead:
        """Update a todo. Only the owner can update."""
        todo = await self._get_todo_or_404(todo_id)
        self._check_owner(todo, current_user_id)

        update_data = todo_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(todo, key, value)

        todo = await self.todo_repository.update(todo)
        return TodoRead.model_validate(todo)

    async def delete_todo(self, todo_id: uuid.UUID, current_user_id: uuid.UUID):
        """Delete a todo. Only the owner can delete."""
        todo = await self._get_todo_or_404(todo_id)
        self._check_owner(todo, current_user_id)
        await self.todo_repository.delete(todo)

    async def toggle_complete(
        self,
        todo_id: uuid.UUID,
        current_user_id: uuid.UUID,
    ) -> TodoRead:
        """Toggle todo completion status. COMPLETED ↔ NOT_STARTED."""
        todo = await self._get_todo_or_404(todo_id)
        self._check_owner(todo, current_user_id)

        todo.status = (
            TodoStatus.COMPLETED
            if todo.status != TodoStatus.COMPLETED
            else TodoStatus.NOT_STARTED
        )
        await self.todo_repository.update(todo)
        return TodoRead.model_validate(todo)

    async def get_statistics(self, user_id: uuid.UUID) -> TodoStatsRead:
        """Get todo statistics for the authenticated user."""
        overall_statistics_row = await self.todo_repository.get_overall_statistics(
            user_id
        )
        statistics_by_priority = await self.todo_repository.get_statistics_by_priority(
            user_id
        )

        return TodoStatsRead(
            total=overall_statistics_row.total,
            completed=overall_statistics_row.completed,
            pending=overall_statistics_row.pending,
            by_priority={row.priority: row.count for row in statistics_by_priority},
        )

    async def _get_todo_or_404(self, todo_id: uuid.UUID) -> Todo:
        """Get a todo by ID or raise 404."""
        todo = await self.todo_repository.get_by_id(todo_id)
        if not todo:
            raise NotFoundException("Todo not found")
        return todo

    @staticmethod
    def _check_owner(todo: Todo, current_user_id: uuid.UUID) -> None:
        """Raise 403 if the current user is not the todo owner."""
        if todo.user_id != current_user_id:
            raise ForbiddenException("Not authorized to access this todo")
