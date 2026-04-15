from app.models import Finding
from app.scanners.common import run_cmd, normalize_severity
import json
import os

def run(repo_path: str) -> list[Finding]:
    findings = []
    
    # Check if requirements.txt exists since safety requires it explicitly
    req_path = os.path.join(repo_path, 'requirements.txt')
    if not os.path.exists(req_path):
        return findings

    out, _, _ = run_cmd(
        ['safety', 'check', '-r', 'requirements.txt', '--json'],
        cwd=repo_path,
    )
    
    if not out.strip():
        return findings

    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return findings

    # Depending on safety version, its a dict with 'vulnerabilities' or a list of lists 
    vulnerabilities = data.get('vulnerabilities', []) if isinstance(data, dict) else data

    for vuln in vulnerabilities:
        if isinstance(vuln, dict):
            # new format
            f = Finding(
                tool         = 'safety',
                rule_id      = vuln.get('vulnerability_id', ''),
                severity     = normalize_severity(vuln.get('severity', 'HIGH')),
                file_path    = 'requirements.txt',
                message      = f"Vulnerable package {vuln.get('package_name', '')}",
                code_snippet = vuln.get('advisory', ''),
            )
            findings.append(f)
        elif isinstance(vuln, list) and len(vuln) >= 5:
            # old format: [package_name, vulnerable_version, safe_version, advisory, cve]
            f = Finding(
                tool         = 'safety',
                rule_id      = vuln[4] if len(vuln) > 4 else '',
                severity     = 'HIGH',
                file_path    = 'requirements.txt',
                message      = f"Vulnerable package {vuln[0]}",
                code_snippet = vuln[3] if len(vuln) > 3 else '',
            )
            findings.append(f)

    return findings
