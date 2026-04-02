from app.models import Finding
from app.extensions import db
import json
from .common import run_cmd, normalize_severity
from loguru import logger

def run(repo_path: str, commit_sha: str) -> list[Finding]:
    findings = []
    out, _, _ = run_cmd(
        ['bandit', '-r', '.', '-f', 'json', '-q'],
        cwd=repo_path,
    )
    try: data = json.loads(out)
    except json.JSONDecodeError: return

    for result in data.get('results', []):
        f = Finding(
            commit_sha   = commit_sha,
            tool         = 'bandit',
            rule_id      = result.get('test_id'),
            severity     = normalize_severity(result.get('issue_severity', '')),
            confidence   = result.get('issue_confidence', ''),
            file_path    = result.get('filename', '').replace(repo_path, '').lstrip('/'),
            line_start   = result.get('line_number'),
            line_end     = result.get('line_range', [None])[-1],
            message      = result.get('issue_text', ''),
            code_snippet = result.get('code', ''),
            cwe          = result.get('issue_cwe', {}).get('id', ''),
        )
        findings.append(f)
    logger.debug(f'Scan data: {data}')
    logger.debug(f'Findings: {findings}')
    db.session.add_all(findings)
    db.session.commit()




