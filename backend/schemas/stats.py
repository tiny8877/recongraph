from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_subdomains: int = 0
    total_urls: int = 0
    total_params: int = 0
    total_findings: int = 0
    params_by_attack: dict[str, int] = {}
    status_codes: dict[str, int] = {}
    top_params: list[dict] = []
    technologies: list[dict] = []
    nuclei_summary: dict[str, int] = {}
