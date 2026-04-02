from app.models import Finding
from app.scanners.common import run_cmd, normalize_severity
import tempfile
import json


def run(repo_path: str) -> list[Finding]:
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        output_path = tmp_file.name
        findings = []
        out, _, _ = run_cmd(
            ['nodejsscan', '.', '--json', '-o', output_path],
            cwd=repo_path,
        )
        with open(output_path, 'r') as f:
            data = json.load(f)

        for severity_key in ('nodejs', 'template_injection', 'misc_issues'):
            for title, issues in (data.get(severity_key) or {}).items():
                for issue in (issues if isinstance(issues,list) else [issues]):
                    # For every file, it will be a seperate entry in the findings table, even if they are the same issue (same title and description)
                    metadata = issue.get('metadata', {})
                    for file_info in issue.get('files', []):
                        f = Finding(
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


