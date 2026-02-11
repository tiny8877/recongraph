from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Subdomain


async def parse_subfinder(project_id: str, content: str, db: AsyncSession) -> dict:
    """Parse subfinder/amass output (one subdomain per line)."""
    lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
    parsed_count = len(lines)
    new_count = 0
    duplicate_count = 0

    for line in lines:
        subdomain_str = line.lower().strip()
        # Skip invalid lines
        if " " in subdomain_str or not "." in subdomain_str:
            continue

        # Check for duplicate
        existing = await db.execute(
            select(Subdomain).where(
                Subdomain.project_id == project_id,
                Subdomain.subdomain == subdomain_str,
            )
        )
        if existing.scalar_one_or_none():
            duplicate_count += 1
            continue

        sub = Subdomain(
            project_id=project_id,
            subdomain=subdomain_str,
            source="subfinder",
        )
        db.add(sub)
        new_count += 1

    await db.commit()
    return {"parsed_count": parsed_count, "new_count": new_count, "duplicate_count": duplicate_count}
