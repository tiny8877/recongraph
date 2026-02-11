from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession


class BaseParser(ABC):
    @abstractmethod
    async def parse(self, project_id: str, content: str, db: AsyncSession) -> dict:
        """Parse tool output and save to database.
        Returns: { parsed_count, new_count, duplicate_count }
        """
        ...
