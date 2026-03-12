from app.models import Finding
import json
from .common import run_cmd, normalize_severity


def run(repo_path: str, scan_id: int) -> list[Finding]:
    findings = []
    out, _, _ = run_cmd(
        ['nodejsscan', '-d', '.', '-o', '/tmp/nodejsscan_out.json'],
        cwd=repo_path,
    )
    try:
        with open('/tmp/nodejsscan_out.json') as fh:
            data = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return findings

    for severity_key in ('nodejs_issues', 'template_injection', 'misc_issues'):
        for title, issues in (data.get(severity_key) or {}).items():
            for issue in (issues if isinstance(issues, list) else [issues]):
                f = Finding(
                    scan_run_id=scan_id,
                    tool='nodejsscan',
                    rule_id=title,
                    severity=normalize_severity(issue.get('level', 'MEDIUM')),
                    file_path=issue.get('filename', '').replace(repo_path, '').lstrip('/'),
                    line_start=issue.get('line'),
                    message=issue.get('description', title),
                    code_snippet=issue.get('lines', ''),
                    owasp=issue.get('tag', ''),
                )
                findings.append(f)
    return findings
