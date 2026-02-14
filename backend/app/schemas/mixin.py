from datetime import datetime
from pydantic import BaseModel


class TimeStampReadMixin(BaseModel):
    """Read-only timestamp fields for response schemas (no SA column config)."""

    created_at: datetime
    updated_at: datetime