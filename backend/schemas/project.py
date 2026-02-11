from datetime import datetime
from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    root_domain: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    root_domain: str
    created_at: datetime
    subdomain_count: int = 0
    url_count: int = 0
    param_count: int = 0
    finding_count: int = 0

    class Config:
        from_attributes = True
