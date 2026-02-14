import uuid
from collections.abc import Sequence
from sqlalchemy import Row
from sqlmodel import select, func
from app.models.todo import Todo, Priority, TodoStatus
from app.repositories.base import BaseRepository


class TodoRepository(BaseRepository):

    async def create(self, todo: Todo) -> Todo:
        """Create a new todo in the database."""
        self.session.add(todo)
        await self.session.commit()
        await self.session.refresh(todo)
        return todo

    async def get_by_id(self, todo_id: uuid.UUID) -> Todo | None:
        """Get a single todo by ID."""
        return await self.session.get(Todo, todo_id)

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        priority: Priority | None = None,
        completed: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Todo], int]:
        """Get all todos with pagination, filtering, and search."""
        statement = select(Todo).order_by(Todo.created_at.desc(), Todo.id)

        if priority is not None:
            statement = statement.where(Todo.priority == priority)

        if completed is not None:
            complete_status = TodoStatus.COMPLETED
            statement = statement.where(
                Todo.status == complete_status
                if completed
                else Todo.status != complete_status
            )

        if search:
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            statement = statement.where(Todo.title.ilike(f"%{escaped}%"))

        return await self._paginate(statement, page, page_size)

    async def update(self, todo: Todo) -> Todo:
        """Update an existing todo."""
        self.session.add(todo)
        await self.session.commit()
        await self.session.refresh(todo)
        return todo

    async def delete(self, todo: Todo) -> None:
        """Delete a todo from the database."""
        await self.session.delete(todo)
        await self.session.commit()

    async def get_overall_statistics(self, user_id: uuid.UUID) -> Row:
        """Get total, completed, and pending counts for a user."""
        statistics_statement = select(
            func.count().label("total"),
            func.count().filter(Todo.status == TodoStatus.COMPLETED).label("completed"),
            func.count().filter(Todo.status != TodoStatus.COMPLETED).label("pending"),
        ).where(Todo.user_id == user_id)

        return (await self.session.execute(statistics_statement)).one()

    async def get_statistics_by_priority(self, user_id: uuid.UUID) -> Sequence[Row]:
        """Get todo counts grouped by priority for a user."""
        priority_statement = select(
            Todo.priority,
            func.count().label("count"),
        ).where(
            Todo.user_id == user_id,
            Todo.priority.is_not(None)
        ).group_by(Todo.priority)

        return (await self.session.execute(priority_statement)).all()
