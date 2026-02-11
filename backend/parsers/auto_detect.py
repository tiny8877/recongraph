import json
from urllib.parse import urlparse, parse_qs

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Subdomain, URL, Parameter, NucleiFinding
from engine.classifier import classify_parameter


def _detect_line_type(line: str) -> str:
    """Auto-detect the type of a single line of recon data."""
    stripped = line.strip()
    if not stripped:
        return "skip"

    # Try JSON first
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
            if "template-id" in data or "templateID" in data or "info" in data:
                return "nuclei"
            if "status_code" in data or "status-code" in data or "tech" in data or "technologies" in data:
                return "httpx"
            return "json_unknown"
        except json.JSONDecodeError:
            pass

    # URL with parameters → waybackurls type
    if stripped.startswith(("http://", "https://")):
        if "?" in stripped:
            return "url_with_params"
        return "url_no_params"

    # Plain hostname (subdomain)
    if "." in stripped and " " not in stripped and "/" not in stripped:
        return "subdomain"

    return "skip"


async def parse_auto_detect(project_id: str, content: str, db: AsyncSession) -> dict:
    """Smart parser that auto-detects each line's type and processes accordingly."""
    lines = content.strip().splitlines()
    parsed_count = len(lines)
    new_count = 0
    duplicate_count = 0
    breakdown = {
        "subdomains": 0,
        "urls_with_params": 0,
        "urls_no_params": 0,
        "httpx_entries": 0,
        "nuclei_findings": 0,
        "skipped": 0,
    }

    for line in lines:
        stripped = line.strip()
        if not stripped:
            breakdown["skipped"] += 1
            continue

        line_type = _detect_line_type(stripped)

        if line_type == "skip" or line_type == "json_unknown":
            breakdown["skipped"] += 1
            continue

        elif line_type == "subdomain":
            hostname = stripped.lower()
            existing = await db.execute(
                select(Subdomain).where(
                    Subdomain.project_id == project_id,
                    Subdomain.subdomain == hostname,
                )
            )
            if existing.scalar_one_or_none():
                duplicate_count += 1
                continue
            db.add(Subdomain(project_id=project_id, subdomain=hostname, source="auto"))
            new_count += 1
            breakdown["subdomains"] += 1

        elif line_type in ("url_with_params", "url_no_params"):
            url_str = stripped
            if not url_str.startswith(("http://", "https://")):
                url_str = "https://" + url_str

            try:
                parsed = urlparse(url_str)
            except Exception:
                breakdown["skipped"] += 1
                continue

            hostname = parsed.hostname
            if not hostname:
                breakdown["skipped"] += 1
                continue

            # Ensure subdomain exists
            sub_result = await db.execute(
                select(Subdomain).where(
                    Subdomain.project_id == project_id,
                    Subdomain.subdomain == hostname,
                )
            )
            subdomain = sub_result.scalar_one_or_none()
            if not subdomain:
                subdomain = Subdomain(project_id=project_id, subdomain=hostname, source="auto")
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
                source="auto",
            )
            db.add(url_obj)
            await db.flush()

            # Parse params
            query_params = parse_qs(parsed.query, keep_blank_values=True)
            for param_name, values in query_params.items():
                attack_types = classify_parameter(param_name)
                db.add(Parameter(
                    url_id=url_obj.id,
                    project_id=project_id,
                    name=param_name,
                    sample_value=values[0] if values else None,
                    attack_types=attack_types,
                ))

            new_count += 1
            if line_type == "url_with_params":
                breakdown["urls_with_params"] += 1
            else:
                breakdown["urls_no_params"] += 1

        elif line_type == "httpx":
            data = json.loads(stripped)
            host = (data.get("host") or data.get("input") or "").lower().strip()
            if not host:
                breakdown["skipped"] += 1
                continue

            existing = await db.execute(
                select(Subdomain).where(
                    Subdomain.project_id == project_id,
                    Subdomain.subdomain == host,
                )
            )
            subdomain = existing.scalar_one_or_none()
            technologies = data.get("tech") or data.get("technologies") or []
            if not isinstance(technologies, list):
                technologies = [technologies]

            if subdomain:
                subdomain.status_code = data.get("status_code") or data.get("status-code")
                subdomain.title = data.get("title")
                subdomain.ip_address = data.get("host_ip")
                subdomain.content_length = data.get("content_length") or data.get("content-length")
                subdomain.technologies = technologies
                subdomain.source = "httpx"
                duplicate_count += 1
            else:
                db.add(Subdomain(
                    project_id=project_id, subdomain=host,
                    status_code=data.get("status_code") or data.get("status-code"),
                    title=data.get("title"), ip_address=data.get("host_ip"),
                    content_length=data.get("content_length") or data.get("content-length"),
                    technologies=technologies, source="httpx",
                ))
                new_count += 1
            breakdown["httpx_entries"] += 1

        elif line_type == "nuclei":
            data = json.loads(stripped)
            template_id = data.get("template-id") or data.get("templateID") or "unknown"
            name = data.get("info", {}).get("name") or data.get("name") or template_id
            severity = (data.get("info", {}).get("severity") or data.get("severity") or "info").lower()
            matched_at = data.get("matched-at") or data.get("matched") or data.get("host") or ""
            description = data.get("info", {}).get("description") or ""

            # Link to subdomain
            subdomain_id = None
            try:
                hostname = urlparse(matched_at).hostname
                if hostname:
                    sub = (await db.execute(
                        select(Subdomain).where(
                            Subdomain.project_id == project_id,
                            Subdomain.subdomain == hostname,
                        )
                    )).scalar_one_or_none()
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

            db.add(NucleiFinding(
                project_id=project_id, subdomain_id=subdomain_id,
                template_id=template_id, name=name, severity=severity,
                matched_at=matched_at, description=description,
            ))
            new_count += 1
            breakdown["nuclei_findings"] += 1

    await db.commit()
    return {
        "parsed_count": parsed_count,
        "new_count": new_count,
        "duplicate_count": duplicate_count,
        "breakdown": breakdown,
    }
