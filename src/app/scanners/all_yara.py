from app.models import Finding
from app.scanners.common import run_cmd
import os

def run(repo_path: str) -> list[Finding]:
    findings = []
    
    # Path to the yara_rules directory relative to this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    rules_index = os.path.join(current_dir, 'yara_rules', 'index.yar')
    
    if not os.path.exists(rules_index):
        # YARA rules have not been downloaded/setup by the user yet
        return findings

    # yara [OPTIONS] RULES_FILE TARGET
    # -r = recursive, -w = disable warnings
    out, _, _ = run_cmd(
        ['yara', '-r', '-w', rules_index, repo_path],
        cwd=repo_path,
    )
    
    if not out.strip():
        return findings

    # Output format is simply:
    # RuleName /path/to/file
    # Sometimes it can have match strings depending on options, but default is just rule and file
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
            
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
            
        rule_name = parts[0]
        file_path = parts[1]
        
        # Clean up absolute file path to be relative to the repo
        clean_file_path = file_path.replace(repo_path, '').lstrip('/\\')

        f = Finding(
            tool         = 'yara',
            rule_id      = rule_name,
            severity     = 'CRITICAL',
            file_path    = clean_file_path,
            message      = f"Malicious Code Detected: {rule_name}",
            code_snippet = "Matched YARA Malware Signature",
        )
        findings.append(f)

    return findings
