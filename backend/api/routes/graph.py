from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.graph import GraphData
from schemas.mindmap import MindmapData
from engine.graph_builder import build_graph
from engine.mindmap_builder import build_mindmap

router = APIRouter()


@router.get("/{project_id}/graph", response_model=GraphData)
async def get_graph_data(
    project_id: str,
    depth: int = Query(default=3, ge=1, le=5),
    attack_type: str | None = Query(default=None),
    limit: int = Query(default=500, ge=10, le=5000),
    min_risk: int = Query(default=0, ge=0, le=10),
    db: AsyncSession = Depends(get_db),
):
    return await build_graph(project_id, db, depth=depth, attack_type=attack_type, limit=limit, min_risk=min_risk)


@router.get("/{project_id}/mindmap", response_model=MindmapData)
async def get_mindmap_data(
    project_id: str,
    attack_type: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    return await build_mindmap(project_id, db, attack_type=attack_type)
