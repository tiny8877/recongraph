import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Subdomain


async def parse_httpx(project_id: str, content: str, db: AsyncSession) -> dict:
    """Parse httpx JSON output (one JSON object per line - JSONL format)."""
    lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
    parsed_count = 0
    new_count = 0
    duplicate_count = 0

    for line in lines:
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        parsed_count += 1
        host = data.get("host") or data.get("input") or ""
        if not host:
            continue

        host = host.lower().strip()

        # Check existing
        existing = await db.execute(
            select(Subdomain).where(
                Subdomain.project_id == project_id,
                Subdomain.subdomain == host,
            )
        )
        subdomain = existing.scalar_one_or_none()

        if subdomain:
            # Update with httpx data
            subdomain.status_code = data.get("status_code") or data.get("status-code")
            subdomain.title = data.get("title")
            subdomain.ip_address = data.get("host") if data.get("a") else data.get("host_ip")
            subdomain.content_length = data.get("content_length") or data.get("content-length")
            technologies = data.get("tech") or data.get("technologies") or []
            subdomain.technologies = technologies if isinstance(technologies, list) else [technologies]
            subdomain.source = "httpx"
            duplicate_count += 1
        else:
            technologies = data.get("tech") or data.get("technologies") or []
            subdomain = Subdomain(
                project_id=project_id,
                subdomain=host,
                status_code=data.get("status_code") or data.get("status-code"),
                title=data.get("title"),
                ip_address=data.get("host_ip"),
                content_length=data.get("content_length") or data.get("content-length"),
                technologies=technologies if isinstance(technologies, list) else [technologies],
                source="httpx",
            )
            db.add(subdomain)
            new_count += 1

    await db.commit()
    return {"parsed_count": parsed_count, "new_count": new_count, "duplicate_count": duplicate_count}
