import csv
import io
import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Subdomain, URL, Parameter

router = APIRouter()


@router.get("/{project_id}/search")
async def search_project(
    project_id: str,
    q: str = Query(..., min_length=1),
    type: str = Query(default="all"),
    db: AsyncSession = Depends(get_db),
):
    results = {"subdomains": [], "urls": [], "params": []}

    if type in ("all", "subdomain"):
        subs = await db.execute(
            select(Subdomain)
            .where(Subdomain.project_id == project_id, Subdomain.subdomain.contains(q))
            .limit(50)
        )
        results["subdomains"] = [
            {"id": s.id, "subdomain": s.subdomain, "status_code": s.status_code, "ip": s.ip_address}
            for s in subs.scalars()
        ]

    if type in ("all", "url"):
        urls = await db.execute(
            select(URL)
            .where(URL.project_id == project_id, URL.full_url.contains(q))
            .limit(50)
        )
        results["urls"] = [
            {"id": u.id, "url": u.full_url, "path": u.path, "source": u.source}
            for u in urls.scalars()
        ]

    if type in ("all", "param"):
        params = await db.execute(
            select(Parameter)
            .where(Parameter.project_id == project_id, Parameter.name.contains(q))
            .limit(50)
        )
        results["params"] = [
            {"id": p.id, "name": p.name, "attack_types": p.attack_types, "sample_value": p.sample_value}
            for p in params.scalars()
        ]

    return results


@router.get("/{project_id}/params")
async def list_params(
    project_id: str,
    attack_type: str | None = Query(default=None),
    sort: str = Query(default="count"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Parameter).where(Parameter.project_id == project_id)
    result = await db.execute(query)
    params = result.scalars().all()

    if attack_type:
        params = [p for p in params if attack_type.upper() in [a.upper() for a in (p.attack_types or [])]]

    # Group by name
    grouped: dict[str, dict] = {}
    for p in params:
        if p.name not in grouped:
            grouped[p.name] = {"name": p.name, "count": 0, "attack_types": set(), "sample_value": p.sample_value}
        grouped[p.name]["count"] += 1
        grouped[p.name]["attack_types"].update(p.attack_types or [])

    items = [{"name": v["name"], "count": v["count"], "attack_types": list(v["attack_types"]), "sample_value": v["sample_value"]} for v in grouped.values()]
    items.sort(key=lambda x: -x["count"])

    start = (page - 1) * limit
    return {"total": len(items), "page": page, "items": items[start:start + limit]}


@router.get("/{project_id}/subdomains")
async def list_subdomains(
    project_id: str,
    status_code: int | None = Query(default=None),
    has_params: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Subdomain).where(Subdomain.project_id == project_id)
    if status_code:
        query = query.where(Subdomain.status_code == status_code)
    query = query.order_by(Subdomain.subdomain).offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    subs = result.scalars().all()

    total = (await db.execute(
        select(func.count(Subdomain.id)).where(Subdomain.project_id == project_id)
    )).scalar() or 0

    items = []
    for s in subs:
        url_count = (await db.execute(
            select(func.count(URL.id)).where(URL.subdomain_id == s.id)
        )).scalar() or 0
        items.append({
            "id": s.id, "subdomain": s.subdomain, "ip_address": s.ip_address,
            "status_code": s.status_code, "title": s.title,
            "technologies": s.technologies, "url_count": url_count, "source": s.source,
        })

    return {"total": total, "page": page, "items": items}


@router.get("/{project_id}/urls")
async def list_urls(
    project_id: str,
    attack_type: str | None = Query(default=None),
    subdomain: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(URL).where(URL.project_id == project_id)

    if subdomain:
        sub_result = await db.execute(
            select(Subdomain.id).where(Subdomain.project_id == project_id, Subdomain.subdomain == subdomain)
        )
        sub_id = sub_result.scalar_one_or_none()
        if sub_id:
            query = query.where(URL.subdomain_id == sub_id)

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    urls = result.scalars().all()

    items = []
    for u in urls:
        param_result = await db.execute(
            select(Parameter).where(Parameter.url_id == u.id)
        )
        params = param_result.scalars().all()

        if attack_type and not any(attack_type.upper() in [a.upper() for a in (p.attack_types or [])] for p in params):
            continue

        items.append({
            "id": u.id, "url": u.full_url, "path": u.path, "source": u.source,
            "params": [{"name": p.name, "attack_types": p.attack_types} for p in params],
        })

    total = (await db.execute(
        select(func.count(URL.id)).where(URL.project_id == project_id)
    )).scalar() or 0

    return {"total": total, "page": page, "items": items}


@router.get("/{project_id}/attack-urls")
async def get_attack_urls(
    project_id: str,
    attack_type: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Get all URLs grouped by attack type with full URL and vulnerable parameters."""
    all_params = (await db.execute(
        select(Parameter).where(Parameter.project_id == project_id)
    )).scalars().all()

    # Group by attack type
    attack_map: dict[str, list[dict]] = {}
    url_cache: dict[str, str] = {}

    for p in all_params:
        if not p.attack_types:
            continue

        # Get URL
        if p.url_id not in url_cache:
            url_obj = (await db.execute(select(URL).where(URL.id == p.url_id))).scalar_one_or_none()
            url_cache[p.url_id] = url_obj.full_url if url_obj else ""
        full_url = url_cache[p.url_id]
        if not full_url:
            continue

        for at in p.attack_types:
            if attack_type and at.upper() != attack_type.upper():
                continue
            if at not in attack_map:
                attack_map[at] = []
            attack_map[at].append({
                "url": full_url,
                "param": p.name,
                "value": p.sample_value,
            })

    # Deduplicate and count
    result = {}
    for at, entries in sorted(attack_map.items()):
        seen = set()
        unique = []
        for e in entries:
            key = f"{e['url']}|{e['param']}"
            if key not in seen:
                seen.add(key)
                unique.append(e)
        result[at] = {
            "count": len(unique),
            "urls": unique,
        }

    return result


@router.get("/{project_id}/export")
async def export_data(
    project_id: str,
    attack_type: str | None = Query(default=None),
    format: str = Query(default="txt"),
    db: AsyncSession = Depends(get_db),
):
    query = select(URL).where(URL.project_id == project_id)
    result = await db.execute(query)
    urls = result.scalars().all()

    filtered_urls = []
    for u in urls:
        if attack_type:
            param_result = await db.execute(select(Parameter).where(Parameter.url_id == u.id))
            params = param_result.scalars().all()
            if any(attack_type.upper() in [a.upper() for a in (p.attack_types or [])] for p in params):
                filtered_urls.append(u.full_url)
        else:
            filtered_urls.append(u.full_url)

    if format == "json":
        return StreamingResponse(
            io.BytesIO(json.dumps(filtered_urls, indent=2).encode()),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=export.json"},
        )
    elif format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["url"])
        for url in filtered_urls:
            writer.writerow([url])
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=export.csv"},
        )
    else:
        content = "\n".join(filtered_urls)
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=export.txt"},
        )
