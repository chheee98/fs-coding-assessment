import uuid
from datetime import datetime
from sqlmodel import SQLModel, Field
from app.models.todo import Priority, TodoStatus
from app.schemas.pagination import PaginatedResponse


class TodoCreate(SQLModel):

    title: str = Field(max_length=200)
    description: str = Field(default="")
    priority: Priority | None = None
    due_date: datetime | None = None


class TodoUpdate(SQLModel):
    title: str = Field(default=None, max_length=200)
    description: str | None = None
    status: TodoStatus | None = None
    priority: Priority | None = None
    due_date: datetime | None = None


class TodoRead(SQLModel):
    id: uuid.UUID
    title: str
    status: TodoStatus
    priority: Priority | None
    due_date: datetime | None
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TodoReadList(SQLModel):
    id: uuid.UUID
    title: str
    description: str | None
    status: TodoStatus
    priority: Priority | None
    due_date: datetime | None
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


TodoPaginatedResponse = PaginatedResponse[TodoReadList]
