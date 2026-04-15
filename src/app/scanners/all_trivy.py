from app.models import Finding
from app.scanners.common import run_cmd, normalize_severity
import tempfile
import json
import os

def run(repo_path: str) -> list[Finding]:
    findings = []
    with tempfile.NamedTemporaryFile(suffix='.json') as tmp_file:
        output_path = tmp_file.name

        out, _, _ = run_cmd(
            ['trivy', 'fs', '--format', 'json', '--output', output_path, '-q', '.'],
            cwd=repo_path,
        )
        
        if not os.path.exists(output_path):
            return findings

        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return findings

        for result in data.get('Results', []):
            target_file = result.get('Target', '').replace(repo_path, '').lstrip('/')
            
            # Parse Vulnerabilities
            for vuln in result.get('Vulnerabilities', []):
                f = Finding(
                    tool         = 'trivy',
                    rule_id      = vuln.get('VulnerabilityID', ''),
                    severity     = normalize_severity(vuln.get('Severity', 'MEDIUM')),
                    file_path    = target_file,
                    message      = f"Vulnerable Package {vuln.get('Title', '')}",
                    code_snippet = vuln.get('Description', ''),
                )
                findings.append(f)
                
            # Parse Misconfigurations
            for misconf in result.get('Misconfigurations', []):
                if misconf.get('Status') == 'PASS': continue
                f = Finding(
                    tool         = 'trivy',
                    rule_id      = misconf.get('ID', ''),
                    severity     = normalize_severity(misconf.get('Severity', 'MEDIUM')),
                    file_path    = target_file,
                    message      = misconf.get('Title', misconf.get('Message', '')),
                    code_snippet = misconf.get('Description', ''),
                )
                findings.append(f)


        return findings
