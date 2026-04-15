from app.models import Finding
from app.scanners.common import run_cmd, normalize_severity
import tempfile
import json
import os

def run(repo_path: str) -> list[Finding]:
    with tempfile.NamedTemporaryFile() as tmp_file:
        output_path = tmp_file.name

        out, _, _ = run_cmd(
            ['gitleaks', 'detect', '--source', '.', '--no-git', '--report-format', 'json', '--report-path', output_path],
            cwd=repo_path,
        )
        
        if not os.path.exists(output_path):
            return []

        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return []
        
        findings = []        
        for leak in data:
            # Gitleaks outputs a list of dictionaries immediately
            f = Finding(
                tool         = 'gitleaks',
                rule_id      = leak.get('RuleID', ''),
                severity     = 'CRITICAL', # Secrets count as critical
                file_path    = leak.get('File', '').replace(repo_path, '').lstrip('/'),
                line_start   = leak.get('StartLine'),
                line_end     = leak.get('EndLine', leak.get('StartLine')),
                message      = leak.get('Description', 'Hardcoded Secret Detected'),
                code_snippet = leak.get('Match', leak.get('Secret', '')),
            )
            findings.append(f)

        return findings
