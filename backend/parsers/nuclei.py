import json
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Subdomain, NucleiFinding


async def parse_nuclei(project_id: str, content: str, db: AsyncSession) -> dict:
    """Parse nuclei JSON output (one JSON object per line - JSONL format)."""
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

        template_id = data.get("template-id") or data.get("templateID") or "unknown"
        name = data.get("info", {}).get("name") or data.get("name") or template_id
        severity = (data.get("info", {}).get("severity") or data.get("severity") or "info").lower()
        matched_at = data.get("matched-at") or data.get("matched") or data.get("host") or ""
        description = data.get("info", {}).get("description") or ""

        # Extract hostname for subdomain linking
        subdomain_id = None
        try:
            hostname = urlparse(matched_at).hostname
            if hostname:
                sub_result = await db.execute(
                    select(Subdomain).where(
                        Subdomain.project_id == project_id,
                        Subdomain.subdomain == hostname,
                    )
                )
                sub = sub_result.scalar_one_or_none()
                if sub:
                    subdomain_id = sub.id
        except Exception:
            pass

        # Check duplicate
        existing = await db.execute(
            select(NucleiFinding).where(
                NucleiFinding.project_id == project_id,
                NucleiFinding.template_id == template_id,
                NucleiFinding.matched_at == matched_at,
            )
        )
        if existing.scalar_one_or_none():
            duplicate_count += 1
            continue

        finding = NucleiFinding(
            project_id=project_id,
            subdomain_id=subdomain_id,
            template_id=template_id,
            name=name,
            severity=severity,
            matched_at=matched_at,
            description=description,
        )
        db.add(finding)
        new_count += 1

    await db.commit()
    return {"parsed_count": parsed_count, "new_count": new_count, "duplicate_count": duplicate_count}
