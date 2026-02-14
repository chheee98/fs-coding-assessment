from datetime import datetime, timezone
from sqlmodel import DateTime, SQLModel, Field


def utcnow_aware() -> datetime:
    return datetime.now(timezone.utc)


class TimeStampMixin(SQLModel):
    """Mixin for automatic created_at and updated_at fields."""

    created_at: datetime = Field(
        sa_type=DateTime(timezone=True),  # Use timezone-aware type
        default_factory=utcnow_aware,
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=utcnow_aware,
        sa_column_kwargs={"onupdate": utcnow_aware},
    )