from app.models import Finding
from app.scanners.common import run_cmd, normalize_severity
import json

def run(repo_path: str) -> list[Finding]:
    findings = []
    out, _, _ = run_cmd(
        ['cargo', 'audit', '--json'],
        cwd=repo_path,
    )
    if not out.strip():
        return findings

    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return findings

    vulnerabilities = data.get('vulnerabilities', {}).get('list', [])
    for vuln in vulnerabilities:
        pkg = vuln.get('package', {})
        advisory = vuln.get('advisory', {})
        
        f = Finding(
            tool         = 'cargo-audit',
            rule_id      = advisory.get('id', ''),
            severity     = 'HIGH', # cargo-audit doesn't heavily classify standard severity in all cases without looking at cvss, assume HIGH for vulnerable packages
            file_path    = 'Cargo.lock',
            message      = f"Vulnerable package {pkg.get('name')} {pkg.get('version')}: {advisory.get('title', '')}",
            code_snippet = advisory.get('description', ''),
        )
        findings.append(f)
        
    return findings
