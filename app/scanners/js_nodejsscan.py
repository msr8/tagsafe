from app.models import Finding
import json
from .common import run_cmd, normalize_severity


def run(repo_path: str, scan_id: int) -> list[Finding]:
    findings = []
    out, _, _ = run_cmd(
        ['nodejsscan', '.', '--json', '-o', '/tmp/nodejsscan_out.json'],
        cwd=repo_path,
    )
    try:
        with open('/tmp/nodejsscan_out.json') as fh:
            data = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return findings


    for severity_key in ('nodejs', 'template_injection', 'misc_issues'):
        for title, issues in (data.get(severity_key) or {}).items():
            for issue in (issues if isinstance(issues,list) else [issues]):
                # For every file, it will be a seperate entry in the findings table, even if they are the same issue (same title and description)
                metadata = issue.get('metadata', {})
                for file_info in issue.get('files', []):
                    f = Finding(
                        scan_run_id  = scan_id,
                        tool         = 'nodejsscan',
                        rule_id      = title,
                        severity     = normalize_severity(metadata.get('level', 'MEDIUM')),
                        file_path    = file_info.get('file_path', '').replace(repo_path, '').lstrip('/'),
                        line_start   = file_info.get('match_lines', [None])[0],
                        line_end     = file_info.get('match_lines', [None])[-1],
                        message      = metadata.get('description', title),
                        code_snippet = file_info.get('match_string', ''),
                        cwe          = metadata.get('cwe', ''),
                        owasp        = metadata.get('owasp-web', ''),
                    )
                    findings.append(f)
    return findings


