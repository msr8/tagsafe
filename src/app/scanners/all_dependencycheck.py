from app.models import Finding
from app.scanners.common import run_cmd, normalize_severity
import tempfile
import json
import os

def run(repo_path: str) -> list[Finding]:
    findings = []
    with tempfile.NamedTemporaryFile(delete=False, dir=repo_path, suffix='.json') as tmp_file:
        output_path = tmp_file.name

        # Check windows/linux
        arg0 = 'dependency-check.bat' if os.name == 'nt' else 'dependency-check.sh'
        out, _, _ = run_cmd(
            [arg0, '--scan', '.', '--format', 'JSON', '--out', output_path, '--noupdate'], # --noupdate so it doesn't take forever, assuming db is updated periodically
            cwd=repo_path,
        )
        
        if not os.path.exists(output_path):
            return findings

        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return findings

        for dep in data.get('dependencies', []):
            target_file = dep.get('filePath', '').replace(repo_path, '').lstrip('/')
            
            for vuln in dep.get('vulnerabilities', []):
                f = Finding(
                    tool         = 'dependencycheck',
                    rule_id      = vuln.get('name', ''),
                    severity     = normalize_severity(vuln.get('severity', 'MEDIUM')),
                    file_path    = target_file,
                    message      = vuln.get('name', ''),
                    code_snippet = vuln.get('description', ''),
                    cwe          = vuln.get('cwe', '')
                )
                findings.append(f)

        return findings
