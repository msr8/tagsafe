from app.models import Finding
from app.scanners.common import run_cmd, normalize_severity
import json

def run(repo_path: str) -> list[Finding]:
    findings = []
    out, _, _ = run_cmd(
        ['brakeman', '-f', 'json', '-q'],
        cwd=repo_path,
    )
    if not out.strip():
        return findings

    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return findings

    for warning in data.get('warnings', []):
        f = Finding(
            tool         = 'brakeman',
            rule_id      = warning.get('warning_type'),
            severity     = normalize_severity(warning.get('confidence', 'Medium')),
            file_path    = warning.get('file', '').replace(repo_path, '').lstrip('/'),
            line_start   = warning.get('line'),
            line_end     = warning.get('line'),
            message      = warning.get('message', ''),
            code_snippet = str(warning.get('code', '')),
        )
        findings.append(f)
    return findings
