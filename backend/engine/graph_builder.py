from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Project, Subdomain, URL, Parameter, NucleiFinding
from schemas.graph import GraphData, GraphNode, GraphEdge
from engine.classifier import get_attack_color, get_risk_score, get_risk_label, get_insight_text, RISK_SEVERITY


async def build_graph(
    project_id: str,
    db: AsyncSession,
    depth: int = 3,
    attack_type: str | None = None,
    limit: int = 500,
    min_risk: int = 0,
) -> GraphData:
    """Build graph nodes and edges for D3.js visualization."""
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    node_ids: set[str] = set()
    total_count = 0

    # Get project
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if not project:
        return GraphData(nodes=[], edges=[], total_nodes=0)

    # Root domain node
    root_id = f"domain-{project.root_domain}"
    nodes.append(GraphNode(
        id=root_id, label=project.root_domain, type="domain",
        color="#00ffff", size=40, data={"root": True},
    ))
    node_ids.add(root_id)

    if depth < 1:
        return GraphData(nodes=nodes, edges=edges, total_nodes=1)

    # Subdomains
    sub_result = await db.execute(
        select(Subdomain).where(Subdomain.project_id == project_id).limit(limit)
    )
    subdomains = sub_result.scalars().all()
    total_count += len(subdomains)

    attack_type_nodes: dict[str, str] = {}  # attack_name -> node_id
    risk_counts: dict[str, int] = {}  # attack_name -> param count

    for sub in subdomains:
        sub_node_id = f"sub-{sub.id}"
        if sub_node_id in node_ids:
            continue

        nodes.append(GraphNode(
            id=sub_node_id, label=sub.subdomain, type="subdomain",
            color="#00aaff", size=25,
            data={
                "ip": sub.ip_address, "status_code": sub.status_code,
                "title": sub.title, "technologies": sub.technologies,
            },
        ))
        node_ids.add(sub_node_id)
        edges.append(GraphEdge(source=root_id, target=sub_node_id, label="has_subdomain"))

        if depth < 2:
            continue

        # URLs for this subdomain
        url_result = await db.execute(
            select(URL).where(URL.subdomain_id == sub.id).limit(50)
        )
        urls = url_result.scalars().all()

        for url_obj in urls:
            # Get params for this URL
            param_result = await db.execute(
                select(Parameter).where(Parameter.url_id == url_obj.id)
            )
            params = param_result.scalars().all()

            # Filter by attack type if specified
            if attack_type:
                has_match = any(
                    attack_type.upper() in [a.upper() for a in (p.attack_types or [])]
                    for p in params
                )
                if not has_match:
                    continue

            if not params:
                continue

            # Filter by min_risk
            url_risk = max((get_risk_score(p.attack_types or []) for p in params), default=0)
            if url_risk < min_risk:
                continue

            url_node_id = f"url-{url_obj.id}"
            if len(nodes) >= limit:
                return GraphData(nodes=nodes, edges=edges, total_nodes=total_count, truncated=True, risk_summary=risk_counts)

            # Aggregate attack types from params
            url_attack_types = list(set(
                at for p in params for at in (p.attack_types or [])
            ))

            # Color URL by risk level
            url_color = '#ff4444' if url_risk >= 8 else '#ff8800' if url_risk >= 5 else '#00ff88'

            nodes.append(GraphNode(
                id=url_node_id, label=url_obj.path or url_obj.full_url[:60],
                type="url", color=url_color, size=15 + url_risk,
                data={
                    "full_url": url_obj.full_url, "source": url_obj.source,
                    "risk_score": url_risk, "attack_types": url_attack_types,
                    "param_count": len(params),
                },
            ))
            node_ids.add(url_node_id)
            edges.append(GraphEdge(source=sub_node_id, target=url_node_id, label="has_url"))

            if depth < 3:
                continue

            # Parameters
            for param in params:
                if attack_type and attack_type.upper() not in [a.upper() for a in (param.attack_types or [])]:
                    continue

                risk_score = get_risk_score(param.attack_types or [])
                if risk_score < min_risk:
                    continue

                insight = get_insight_text(param.name, param.attack_types or [])

                # Color by risk
                param_color = '#ffff00'
                if risk_score >= 8:
                    param_color = '#ff0000'
                elif risk_score >= 6:
                    param_color = '#ff4444'
                elif risk_score >= 4:
                    param_color = '#ff8800'

                param_node_id = f"param-{param.id}"
                if len(nodes) >= limit:
                    return GraphData(nodes=nodes, edges=edges, total_nodes=total_count, truncated=True, risk_summary=risk_counts)

                nodes.append(GraphNode(
                    id=param_node_id, label=param.name, type="parameter",
                    color=param_color, size=10 + (risk_score * 2),
                    data={
                        "value": param.sample_value,
                        "attack_types": param.attack_types,
                        "risk_score": risk_score,
                        "insight": insight,
                        "risk_labels": [get_risk_label(at) for at in (param.attack_types or [])],
                    },
                ))
                node_ids.add(param_node_id)
                edges.append(GraphEdge(source=url_node_id, target=param_node_id, label="has_param"))

                # Attack type nodes
                for at in (param.attack_types or []):
                    at_node_id = f"attack-{at}"
                    risk_counts[at] = risk_counts.get(at, 0) + 1
                    if at_node_id not in node_ids:
                        nodes.append(GraphNode(
                            id=at_node_id, label=get_risk_label(at), type="attack_type",
                            color=get_attack_color(at), size=20 + (RISK_SEVERITY.get(at, 0) * 2),
                            data={"attack": at, "severity": RISK_SEVERITY.get(at, 0), "description": get_risk_label(at)},
                        ))
                        node_ids.add(at_node_id)
                    edges.append(GraphEdge(source=param_node_id, target=at_node_id, label="vuln_to"))

        # Nuclei findings for this subdomain
        finding_result = await db.execute(
            select(NucleiFinding).where(NucleiFinding.subdomain_id == sub.id)
        )
        findings = finding_result.scalars().all()
        for f in findings:
            f_node_id = f"finding-{f.id}"
            if len(nodes) >= limit:
                return GraphData(nodes=nodes, edges=edges, total_nodes=total_count, truncated=True, risk_summary=risk_counts)

            severity_colors = {
                "critical": "#ff0000", "high": "#ff4444",
                "medium": "#ff8800", "low": "#ffaa00", "info": "#00aaff",
            }
            nodes.append(GraphNode(
                id=f_node_id, label=f.name, type="finding",
                color=severity_colors.get(f.severity, "#888888"), size=18,
                data={"severity": f.severity, "template": f.template_id, "matched_at": f.matched_at},
            ))
            node_ids.add(f_node_id)
            edges.append(GraphEdge(source=sub_node_id, target=f_node_id, label="has_finding"))

    return GraphData(
        nodes=nodes, edges=edges, total_nodes=len(nodes),
        truncated=len(nodes) >= limit, risk_summary=risk_counts,
    )
