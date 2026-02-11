from fastapi import APIRouter

from api.routes import projects, upload, graph, stats, search, delete, scanner

api_router = APIRouter(prefix="/api")

api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(upload.router, prefix="/projects", tags=["Upload"])
api_router.include_router(graph.router, prefix="/projects", tags=["Graph"])
api_router.include_router(stats.router, prefix="/projects", tags=["Stats"])
api_router.include_router(search.router, prefix="/projects", tags=["Search"])
api_router.include_router(delete.router, prefix="/projects", tags=["Delete"])
api_router.include_router(scanner.router, prefix="/scanner", tags=["Scanner"])
