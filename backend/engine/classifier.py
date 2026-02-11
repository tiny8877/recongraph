ATTACK_SIGNATURES: dict[str, dict] = {
    "LFI": {
        "params": {
            "file", "path", "page", "include", "dir", "document", "folder",
            "root", "pg", "view", "content", "download", "template", "load",
            "read", "retrieve", "cat", "type", "conf", "log", "filename",
            "filepath", "resource", "loc", "location",
        },
        "color": "#ff4444",
    },
    "XSS": {
        "params": {
            "q", "search", "query", "keyword", "name", "email", "comment",
            "msg", "message", "text", "value", "input", "callback", "data",
            "body", "title", "error", "preview", "html", "content",
            "description", "feedback", "review", "bio", "note",
        },
        "color": "#ff8800",
    },
    "SQLi": {
        "params": {
            "id", "user", "order", "sort", "column", "table", "select",
            "where", "limit", "offset", "group", "having", "union",
            "category", "item", "product", "price", "date", "from", "to",
            "filter", "report", "role", "update", "result", "num",
        },
        "color": "#ff0066",
    },
    "SSRF": {
        "params": {
            "url", "link", "src", "source", "dest", "uri",
            "domain", "feed", "host", "site", "val",
            "proxy", "api", "endpoint", "fetch", "request",
            "imageurl", "imgurl", "webhook",
        },
        "color": "#aa00ff",
    },
    "Open Redirect": {
        "params": {
            "redirect", "next", "return", "goto", "destination",
            "continue", "target", "redir", "returnto", "returnurl",
            "forward", "out", "ref", "location", "checkout_url",
            "return_path", "redirect_uri", "redirect_url",
        },
        "color": "#ffaa00",
    },
    "RCE": {
        "params": {
            "cmd", "exec", "command", "run", "ping", "jump",
            "code", "reg", "do", "func", "arg", "option",
            "process", "step", "function", "req", "feature",
            "exe", "module", "payload", "action", "execute",
        },
        "color": "#ff0000",
    },
    "IDOR": {
        "params": {
            "id", "user_id", "uid", "account", "profile", "order_id",
            "doc", "key", "group", "role", "no", "number",
            "token", "session", "invoice", "receipt", "file_id", "pid",
            "customer_id", "member_id", "record",
        },
        "color": "#00aaff",
    },
}


def classify_parameter(param_name: str) -> list[str]:
    """Classify a URL parameter name into potential attack types."""
    name_lower = param_name.lower().strip()
    matched = []
    for attack_type, info in ATTACK_SIGNATURES.items():
        if name_lower in info["params"]:
            matched.append(attack_type)
    return matched


def get_attack_color(attack_type: str) -> str:
    """Get the color for an attack type."""
    return ATTACK_SIGNATURES.get(attack_type, {}).get("color", "#888888")


def classify_all_params(param_names: list[str]) -> dict[str, list[str]]:
    """Classify a list of parameter names. Returns {param_name: [attack_types]}."""
    return {name: classify_parameter(name) for name in param_names}


RISK_LABELS: dict[str, str] = {
    "RCE": "RCE Possible",
    "SQLi": "SQL Injection Risk",
    "LFI": "Local File Inclusion Risk",
    "XSS": "Cross-Site Scripting Risk",
    "SSRF": "SSRF Possible",
    "Open Redirect": "Open Redirect Risk",
    "IDOR": "Insecure Direct Object Ref",
}

RISK_SEVERITY: dict[str, int] = {
    "RCE": 10,
    "SQLi": 9,
    "SSRF": 8,
    "LFI": 7,
    "IDOR": 6,
    "XSS": 5,
    "Open Redirect": 4,
}


def get_risk_score(attack_types: list[str]) -> int:
    """Calculate a risk score (0-10) based on attack types."""
    if not attack_types:
        return 0
    return max(RISK_SEVERITY.get(at, 1) for at in attack_types)


def get_risk_label(attack_type: str) -> str:
    """Get a human-readable risk label for an attack type."""
    return RISK_LABELS.get(attack_type, attack_type)


def get_insight_text(param_name: str, attack_types: list[str]) -> str:
    """Generate insight text for a parameter with attack types."""
    if not attack_types:
        return ""
    top_attack = max(attack_types, key=lambda at: RISK_SEVERITY.get(at, 0))
    return f"{get_risk_label(top_attack)} via '{param_name}'"
