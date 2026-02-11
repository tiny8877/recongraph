from pydantic import BaseModel


class MindmapUrl(BaseModel):
    full_url: str
    path: str


class MindmapTechnique(BaseModel):
    name: str
    description: str
    payloads: list[str]
    tools: list[str]
    references: list[str]


class MindmapParameter(BaseModel):
    name: str
    risk_score: int
    sample_value: str | None = None
    urls: list[MindmapUrl]
    attack_types: list[str]


class MindmapAttackType(BaseModel):
    attack_type: str
    description: str
    severity: int
    color: str
    param_count: int
    parameters: list[MindmapParameter]
    techniques: list[MindmapTechnique]


class MindmapSummary(BaseModel):
    total_params: int
    total_attack_types: int
    highest_severity: int
    attack_type_counts: dict[str, int]


class MindmapData(BaseModel):
    root_domain: str
    project_name: str
    summary: MindmapSummary
    attack_types: list[MindmapAttackType]
