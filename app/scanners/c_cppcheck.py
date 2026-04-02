from app.models          import Finding
from app.scanners.common import run_cmd

import xml.etree.ElementTree as ET
import tempfile


def get_code_snippet(locs) -> str:
    diff_files = set([ l.get('file', '') for l in locs ])
    # filename -> string to be displayed
    code_snippets = {}

    for filename in diff_files:
        target_lines = set([ int(l.get('line', 0)) for l in locs if l.get('file', '') == filename ])
        windows = [ (line-3, line+3) for line in target_lines ]

        # Merge overlapping windows
        windows.sort()
        merged_windows = []
        current_start, current_end = windows[0]
        for start,end in windows[1:]:
            # If overlaps with current window
            if start <= current_end:
                current_end = max(current_end, end)
            else:
                merged_windows.append((current_start, current_end))
                current_start, current_end = start, end
        merged_windows.append((current_start, current_end))

        # Read the file and extract the snippets
        snippets = []
        with open(filename, 'r') as f:
            lines = f.readlines()
            for start,end in merged_windows:
                # Adjust for 0-based index and file length
                start_idx = max(0, start-1)
                end_idx = min(len(lines), end)
                snippet = ''.join(lines[start_idx:end_idx])
                snippets.append(snippet)
        
        code_snippets[filename] = '\n.....\n'.join(snippets)
    
    # Combine snippets from all files (if multiple)
    return '\n\n─────────────────────────\n\n'.join([ f"{filename}:\n{snippet}" for filename, snippet in code_snippets.items() ])





def run(repo_path: str) -> list[Finding]:
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        output_path = tmp_file.name
    findings = []
    out, _, _ = run_cmd(
        ['cppcheck', '--enable=all', '--output-file=' + output_path, '--output-format=xmlv3', '--quiet', '-suppress=ctuOneDefinitionRuleViolation', '.'],
        cwd=repo_path,
    )
    try:
        tree = ET.parse(output_path)
        root = tree.getroot()
    except Exception:
        return findings

    for error in root.iter('error'):
        loc = error.find('location')
        locs = error.findall('location')
        severity_raw = error.get('severity', 'information')
        severity_map = {
            'error': 'HIGH',
            'warning': 'MEDIUM',
            'style': 'LOW',
            'performance': 'LOW',
            'portability': 'LOW',
            'information': 'INFO',
        }

        f = Finding(
            tool         = 'cppcheck',
            rule_id      = error.get('id'),
            severity     = severity_map.get(severity_raw, 'INFO'),
            file_path    = (loc.get('file', '') if loc is not None else '').replace(repo_path, '').lstrip('/'),
            line_start   = int(loc.get('line', 0)) if loc is not None else None,
            message      = error.get('msg', ''),
            cwe          = error.get('cwe', ''),
            code_snippet = get_code_snippet(locs)
        )
        findings.append(f)
    return findings