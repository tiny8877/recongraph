from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # domain, subdomain, url, parameter, attack_type, finding
    color: str
    size: int
    data: dict = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str = ""


class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    total_nodes: int
    truncated: bool = False
    risk_summary: dict = {}
