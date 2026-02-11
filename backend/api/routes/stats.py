from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Subdomain, URL, Parameter, NucleiFinding
from schemas.stats import DashboardStats

router = APIRouter()


@router.get("/{project_id}/stats", response_model=DashboardStats)
async def get_project_stats(project_id: str, db: AsyncSession = Depends(get_db)):
    total_subs = (await db.execute(
        select(func.count(Subdomain.id)).where(Subdomain.project_id == project_id)
    )).scalar() or 0

    total_urls = (await db.execute(
        select(func.count(URL.id)).where(URL.project_id == project_id)
    )).scalar() or 0

    total_params = (await db.execute(
        select(func.count(Parameter.id)).where(Parameter.project_id == project_id)
    )).scalar() or 0

    total_findings = (await db.execute(
        select(func.count(NucleiFinding.id)).where(NucleiFinding.project_id == project_id)
    )).scalar() or 0

    # Params by attack type
    params_result = await db.execute(
        select(Parameter.attack_types).where(Parameter.project_id == project_id)
    )
    attack_counts: dict[str, int] = {}
    for (attack_types_json,) in params_result:
        if attack_types_json:
            for at in attack_types_json:
                attack_counts[at] = attack_counts.get(at, 0) + 1

    # Status codes
    status_result = await db.execute(
        select(Subdomain.status_code, func.count(Subdomain.id))
        .where(Subdomain.project_id == project_id, Subdomain.status_code.isnot(None))
        .group_by(Subdomain.status_code)
    )
    status_codes = {str(code): count for code, count in status_result}

    # Top params
    param_names_result = await db.execute(
        select(Parameter.name, func.count(Parameter.id).label("cnt"))
        .where(Parameter.project_id == project_id)
        .group_by(Parameter.name)
        .order_by(func.count(Parameter.id).desc())
        .limit(10)
    )
    top_params = [{"name": name, "count": cnt} for name, cnt in param_names_result]

    # Technologies
    tech_result = await db.execute(
        select(Subdomain.technologies).where(
            Subdomain.project_id == project_id, Subdomain.technologies.isnot(None)
        )
    )
    tech_counts: dict[str, int] = {}
    for (techs,) in tech_result:
        if isinstance(techs, list):
            for t in techs:
                tech_counts[t] = tech_counts.get(t, 0) + 1
        elif isinstance(techs, dict):
            for t in techs:
                tech_counts[t] = tech_counts.get(t, 0) + 1

    technologies = [{"name": k, "count": v} for k, v in sorted(tech_counts.items(), key=lambda x: -x[1])[:10]]

    # Nuclei summary
    nuclei_result = await db.execute(
        select(NucleiFinding.severity, func.count(NucleiFinding.id))
        .where(NucleiFinding.project_id == project_id)
        .group_by(NucleiFinding.severity)
    )
    nuclei_summary = {sev: count for sev, count in nuclei_result}

    return DashboardStats(
        total_subdomains=total_subs,
        total_urls=total_urls,
        total_params=total_params,
        total_findings=total_findings,
        params_by_attack=attack_counts,
        status_codes=status_codes,
        top_params=top_params,
        technologies=technologies,
        nuclei_summary=nuclei_summary,
    )
