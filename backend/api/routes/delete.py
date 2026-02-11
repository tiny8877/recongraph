from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Subdomain, URL, Parameter, NucleiFinding

router = APIRouter()


@router.delete("/{project_id}/subdomains/{subdomain_id}")
async def delete_subdomain(project_id: str, subdomain_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subdomain).where(Subdomain.id == subdomain_id, Subdomain.project_id == project_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subdomain not found")
    await db.delete(sub)
    await db.commit()
    return {"message": "Subdomain deleted", "id": subdomain_id}


@router.delete("/{project_id}/urls/{url_id}")
async def delete_url(project_id: str, url_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(URL).where(URL.id == url_id, URL.project_id == project_id)
    )
    url = result.scalar_one_or_none()
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    await db.delete(url)
    await db.commit()
    return {"message": "URL deleted", "id": url_id}


@router.delete("/{project_id}/parameters/{param_id}")
async def delete_parameter(project_id: str, param_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Parameter).where(Parameter.id == param_id, Parameter.project_id == project_id)
    )
    param = result.scalar_one_or_none()
    if not param:
        raise HTTPException(status_code=404, detail="Parameter not found")
    await db.delete(param)
    await db.commit()
    return {"message": "Parameter deleted", "id": param_id}


@router.delete("/{project_id}/findings/{finding_id}")
async def delete_finding(project_id: str, finding_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NucleiFinding).where(NucleiFinding.id == finding_id, NucleiFinding.project_id == project_id)
    )
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    await db.delete(finding)
    await db.commit()
    return {"message": "Finding deleted", "id": finding_id}


@router.delete("/{project_id}/clear")
async def clear_project_data(project_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Parameter).where(Parameter.project_id == project_id))
    await db.execute(delete(NucleiFinding).where(NucleiFinding.project_id == project_id))
    await db.execute(delete(URL).where(URL.project_id == project_id))
    await db.execute(delete(Subdomain).where(Subdomain.project_id == project_id))
    await db.commit()
    return {"message": "All project data cleared"}


@router.delete("/{project_id}/urls-by-attack")
async def delete_urls_by_attack(
    project_id: str,
    attack_type: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    params = (await db.execute(
        select(Parameter).where(Parameter.project_id == project_id)
    )).scalars().all()

    url_ids_to_delete = set()
    for p in params:
        if attack_type.upper() in [a.upper() for a in (p.attack_types or [])]:
            url_ids_to_delete.add(p.url_id)

    deleted_count = 0
    for url_id in url_ids_to_delete:
        url = (await db.execute(select(URL).where(URL.id == url_id))).scalar_one_or_none()
        if url:
            await db.delete(url)
            deleted_count += 1

    await db.commit()
    return {"message": f"Deleted {deleted_count} URLs", "deleted_count": deleted_count}
