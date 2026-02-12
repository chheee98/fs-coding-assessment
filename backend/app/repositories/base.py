from typing import Any

from sqlalchemy import func, Select
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


class BaseRepository:
    """Base repository with shared database helpers."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _paginate(
        self, statement: Select[Any], page: int, page_size: int
    ) -> tuple[list[Any], int]:
        """Reusable pagination for any query.

        Returns a tuple of (items, total_count).
        """
        count_statement = select(func.count()).select_from(statement.subquery())
        total = (await self.session.execute(count_statement)).scalar_one()

        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)
        results = await self.session.execute(statement)

        return list(results.scalars().all()), total