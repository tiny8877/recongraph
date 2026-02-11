from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Project, Subdomain, URL, Parameter, NucleiFinding
from schemas.project import ProjectCreate, ProjectResponse

router = APIRouter()


@router.post("/", response_model=ProjectResponse)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(name=data.name, root_domain=data.root_domain)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        root_domain=project.root_domain,
        created_at=project.created_at,
    )


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()

    responses = []
    for p in projects:
        sub_count = (await db.execute(select(func.count(Subdomain.id)).where(Subdomain.project_id == p.id))).scalar() or 0
        url_count = (await db.execute(select(func.count(URL.id)).where(URL.project_id == p.id))).scalar() or 0
        param_count = (await db.execute(select(func.count(Parameter.id)).where(Parameter.project_id == p.id))).scalar() or 0
        finding_count = (await db.execute(select(func.count(NucleiFinding.id)).where(NucleiFinding.project_id == p.id))).scalar() or 0
        responses.append(ProjectResponse(
            id=p.id, name=p.name, root_domain=p.root_domain, created_at=p.created_at,
            subdomain_count=sub_count, url_count=url_count, param_count=param_count, finding_count=finding_count,
        ))
    return responses


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    sub_count = (await db.execute(select(func.count(Subdomain.id)).where(Subdomain.project_id == project_id))).scalar() or 0
    url_count = (await db.execute(select(func.count(URL.id)).where(URL.project_id == project_id))).scalar() or 0
    param_count = (await db.execute(select(func.count(Parameter.id)).where(Parameter.project_id == project_id))).scalar() or 0
    finding_count = (await db.execute(select(func.count(NucleiFinding.id)).where(NucleiFinding.project_id == project_id))).scalar() or 0

    return ProjectResponse(
        id=project.id, name=project.name, root_domain=project.root_domain, created_at=project.created_at,
        subdomain_count=sub_count, url_count=url_count, param_count=param_count, finding_count=finding_count,
    )


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
    return {"message": "Project deleted"}
