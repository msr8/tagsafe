from app.models import Finding
import json
from .common import run_cmd, normalize_severity


def get_code_snippet(file_path:str, line_start:int, line_end:int) -> str:
    with open(file_path, 'r') as f:
        lines = f.readlines()
        # Adjust for 0-based index and file length
        start_idx = max(0, line_start-1)
        end_idx = min(len(lines), line_end)
        snippet = ''.join(lines[start_idx:end_idx])
    return snippet


def run(repo_path: str, scan_id: int) -> list[Finding]:
    findings = []
    out, _, _ = run_cmd(
        ['semgrep', 'scan', '--config=auto', '--json-output=/tmp/semgrep.json', '--quiet', '.'],
        cwd=repo_path,
        timeout=600,
    )
    try: data = json.loads(out)
    except json.JSONDecodeError: return findings

    for result in data.get('results', []):
        meta = result.get('extra', {}).get('metadata', {})
        f = Finding(
            scan_run_id  = scan_id,
            tool         = 'semgrep',
            rule_id      = result.get('check_id', ''),
            severity     = normalize_severity(result.get('extra', {}).get('severity', '')),
            file_path    = result.get('path', '').replace(repo_path, '').lstrip('/'),
            line_start   = result.get('start', {}).get('line'),
            line_end     = result.get('end', {}).get('line'),
            message      = result.get('extra', {}).get('message', ''),
            code_snippet = get_code_snippet(
                                file_path    = result.get('path', '').replace(repo_path, '').lstrip('/'),
                                line_start   = result.get('start', {}).get('line'),
                                line_end     = result.get('end', {}).get('line')
                            ),
            cwe          = ','.join(meta.get('cwe', []))   if isinstance(meta.get('cwe'),   list) else meta.get('cwe', ''),
            owasp        = ','.join(meta.get('owasp', [])) if isinstance(meta.get('owasp'), list) else meta.get('owasp', ''),
        )
        findings.append(f)
    return findings