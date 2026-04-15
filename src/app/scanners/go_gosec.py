from app.models import Finding
import json
from .common import run_cmd, normalize_severity

def run(repo_path: str) -> list[Finding]:
    findings = []
    out, _, _ = run_cmd(
        ['gosec', '-fmt=json', '-quiet', './...'],
        cwd=repo_path,
    )
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return findings

    for issue in data.get('Issues', []):
        f = Finding(
            tool         = 'gosec',
            rule_id      = issue.get('rule_id'),
            severity     = normalize_severity(issue.get('severity', '')),
            confidence   = issue.get('confidence', ''),
            file_path    = issue.get('file', '').replace(repo_path, '').lstrip('/'),
            line_start   = int(issue.get('line', 0) or 0),
            message      = issue.get('details', ''),
            cwe          = issue.get('cwe', {}).get('id', '') if isinstance(issue.get('cwe'), dict) else issue.get('cwe', ''),
            code_snippet = issue.get('code', '')
        )
        findings.append(f)
    return findings


