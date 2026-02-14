"""Reusable custom Pydantic types for schema fields."""

from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, FutureDatetime


def normalize_naive(v: datetime) -> datetime:
    """Strip timezone — DB columns are timezone-naive."""
    return v.replace(tzinfo=None) if v.tzinfo else v


NaiveFutureDatetime = Annotated[FutureDatetime, AfterValidator(normalize_naive)]
NaiveDatetime = Annotated[datetime, AfterValidator(normalize_naive)]
