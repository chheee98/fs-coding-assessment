import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.todo import Priority, TodoStatus
from app.schemas.mixin import TimeStampReadMixin
from app.schemas.pagination import PaginatedResponse
from app.schemas.types import NaiveFutureDatetime, NaiveDatetime


class TodoCreate(BaseModel):

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="")
    priority: Priority | None = None
    due_date: NaiveFutureDatetime | None = None


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TodoStatus | None = None
    priority: Priority | None = None
    due_date: NaiveDatetime | None = None

    @field_validator("title", "description", "status", mode="before")
    @classmethod
    def reject_null(cls, v):
        """Reject explicit null for DB non-nullable fields. Omitting the field is fine (partial update)."""
        if v is None:
            raise ValueError("cannot be null")
        return v


class TodoRead(TimeStampReadMixin):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    status: TodoStatus
    priority: Priority | None
    due_date: datetime | None
    user_id: uuid.UUID


class TodoReadList(TimeStampReadMixin):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    status: TodoStatus
    priority: Priority | None
    due_date: datetime | None
    user_id: uuid.UUID


class TodoPriorityStats(BaseModel):
    LOW: int = 0
    MEDIUM: int = 0
    HIGH: int = 0


class TodoStatsRead(BaseModel):
    total: int = 0
    completed: int = 0
    pending: int = 0
    by_priority: TodoPriorityStats = TodoPriorityStats()


TodoPaginatedResponse = PaginatedResponse[TodoReadList]
