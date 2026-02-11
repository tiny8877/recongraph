from datetime import datetime
from pydantic import BaseModel


class ScanRequest(BaseModel):
    project_id: str | None = None
    project_name: str | None = None
    target_domain: str
    scan_type: str = "full_auto"


class ScanJobResponse(BaseModel):
    id: str
    project_id: str
    scan_type: str
    target: str
    status: str
    current_step: str | None = None
    progress: int = 0
    log: str | None = None
    result_summary: dict | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ToolStatus(BaseModel):
    name: str
    installed: bool
    path: str | None = None
    version: str | None = None
