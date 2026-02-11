"""Build hierarchical mindmap data grouped by attack type."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Project, Parameter, URL
from engine.classifier import get_risk_score, RISK_SEVERITY
from engine.attack_knowledge import ATTACK_KNOWLEDGE
from schemas.mindmap import (
    MindmapData,
    MindmapAttackType,
    MindmapParameter,
    MindmapUrl,
    MindmapTechnique,
    MindmapSummary,
)


async def build_mindmap(
    project_id: str,
    db: AsyncSession,
    attack_type: str | None = None,
) -> MindmapData:
    """Build hierarchical mindmap: attack_type -> params -> URLs."""

    # Fetch project
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        return MindmapData(
            root_domain="unknown",
            project_name="unknown",
            summary=MindmapSummary(
                total_params=0,
                total_attack_types=0,
                highest_severity=0,
                attack_type_counts={},
            ),
            attack_types=[],
        )

    # Fetch all parameters with their URLs
    param_query = select(Parameter, URL).join(URL, Parameter.url_id == URL.id).where(
        Parameter.project_id == project_id
    )
    result = await db.execute(param_query)
    rows = result.all()

    # Group by attack type
    # Structure: { attack_type: { param_name: { "sample_value": ..., "attack_types": [...], "urls": [...] } } }
    grouped: dict[str, dict[str, dict]] = {}

    for param, url in rows:
        param_attacks = param.attack_types or []
        if not param_attacks:
            continue

        for at in param_attacks:
            if attack_type and at.lower() != attack_type.lower():
                continue

            if at not in grouped:
                grouped[at] = {}

            if param.name not in grouped[at]:
                grouped[at][param.name] = {
                    "sample_value": param.sample_value,
                    "attack_types": list(set(param_attacks)),
                    "urls": [],
                    "url_set": set(),
                }

            # Deduplicate URLs within each attack type + param
            if url.full_url not in grouped[at][param.name]["url_set"]:
                grouped[at][param.name]["url_set"].add(url.full_url)
                grouped[at][param.name]["urls"].append(
                    MindmapUrl(full_url=url.full_url, path=url.path)
                )

    # Build MindmapAttackType list
    attack_type_list: list[MindmapAttackType] = []
    total_params = 0
    attack_type_counts: dict[str, int] = {}

    for at_name, params_dict in grouped.items():
        knowledge = ATTACK_KNOWLEDGE.get(at_name, {})
        severity = knowledge.get("severity", RISK_SEVERITY.get(at_name, 1))
        color = knowledge.get("color", "#888888")
        description = knowledge.get("description", at_name)

        # Build parameters
        param_list: list[MindmapParameter] = []
        for p_name, p_data in params_dict.items():
            risk = get_risk_score(p_data["attack_types"])
            param_list.append(
                MindmapParameter(
                    name=p_name,
                    risk_score=risk,
                    sample_value=p_data["sample_value"],
                    urls=p_data["urls"],
                    attack_types=p_data["attack_types"],
                )
            )
        # Sort params by risk desc
        param_list.sort(key=lambda p: p.risk_score, reverse=True)

        # Build techniques from knowledge base
        technique_list: list[MindmapTechnique] = []
        for tech in knowledge.get("techniques", []):
            technique_list.append(
                MindmapTechnique(
                    name=tech["name"],
                    description=tech["description"],
                    payloads=tech["payloads"],
                    tools=tech["tools"],
                    references=tech["references"],
                )
            )

        attack_type_counts[at_name] = len(param_list)
        total_params += len(param_list)

        attack_type_list.append(
            MindmapAttackType(
                attack_type=at_name,
                description=description,
                severity=severity,
                color=color,
                param_count=len(param_list),
                parameters=param_list,
                techniques=technique_list,
            )
        )

    # Sort by severity desc (RCE first)
    attack_type_list.sort(key=lambda a: a.severity, reverse=True)

    highest_severity = max((a.severity for a in attack_type_list), default=0)

    return MindmapData(
        root_domain=project.root_domain,
        project_name=project.name,
        summary=MindmapSummary(
            total_params=total_params,
            total_attack_types=len(attack_type_list),
            highest_severity=highest_severity,
            attack_type_counts=attack_type_counts,
        ),
        attack_types=attack_type_list,
    )
