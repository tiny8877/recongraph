from urllib.parse import urlparse, parse_qs

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Subdomain, URL, Parameter
from engine.classifier import classify_parameter


async def parse_waybackurls(project_id: str, content: str, db: AsyncSession) -> dict:
    """Parse waybackurls/gau/katana output (one URL per line)."""
    lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
    parsed_count = len(lines)
    new_count = 0
    duplicate_count = 0

    for line in lines:
        url_str = line.strip()
        if not url_str.startswith(("http://", "https://")):
            url_str = "https://" + url_str

        try:
            parsed = urlparse(url_str)
        except Exception:
            continue

        hostname = parsed.hostname
        if not hostname:
            continue

        # Check/create subdomain
        sub_result = await db.execute(
            select(Subdomain).where(
                Subdomain.project_id == project_id,
                Subdomain.subdomain == hostname,
            )
        )
        subdomain = sub_result.scalar_one_or_none()
        if not subdomain:
            subdomain = Subdomain(project_id=project_id, subdomain=hostname, source="waybackurls")
            db.add(subdomain)
            await db.flush()

        # Check duplicate URL
        existing_url = await db.execute(
            select(URL).where(URL.project_id == project_id, URL.full_url == url_str)
        )
        if existing_url.scalar_one_or_none():
            duplicate_count += 1
            continue

        url_obj = URL(
            project_id=project_id,
            subdomain_id=subdomain.id,
            full_url=url_str,
            path=parsed.path or "/",
            source="waybackurls",
        )
        db.add(url_obj)
        await db.flush()

        # Parse and classify parameters
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        for param_name, values in query_params.items():
            attack_types = classify_parameter(param_name)
            param = Parameter(
                url_id=url_obj.id,
                project_id=project_id,
                name=param_name,
                sample_value=values[0] if values else None,
                attack_types=attack_types,
            )
            db.add(param)

        new_count += 1

    await db.commit()
    return {"parsed_count": parsed_count, "new_count": new_count, "duplicate_count": duplicate_count}
