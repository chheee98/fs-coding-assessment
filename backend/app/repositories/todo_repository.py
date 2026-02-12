import uuid
from sqlmodel import select
from app.models.todo import Todo, Priority, TodoStatus
from app.repositories.base import BaseRepository


class TodoRepository(BaseRepository):

    async def create(self, todo: Todo) -> Todo:
        self.session.add(todo)
        await self.session.commit()
        await self.session.refresh(todo)
        return todo

    async def get_by_id(self, todo_id: uuid.UUID) -> Todo | None:
        return await self.session.get(Todo, todo_id)

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        priority: Priority | None = None,
        completed: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Todo], int]:
        statement = select(Todo)

        if priority:
            statement = statement.where(Todo.priority == priority)

        if completed is not None:
            complete_status = TodoStatus.COMPLETED
            statement = statement.where(
                Todo.status == complete_status
                if completed
                else Todo.status != complete_status
            )

        if search:
            statement = statement.where(Todo.title.ilike(f"%{search}%"))

        return await self._paginate(statement, page, page_size)

    async def update(self, todo: Todo) -> Todo:
        self.session.add(todo)
        await self.session.commit()
        await self.session.refresh(todo)
        return todo

    async def delete(self, todo: Todo) -> None:
        await self.session.delete(todo)
        await self.session.commit()