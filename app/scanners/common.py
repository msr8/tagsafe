import subprocess

def run_cmd(cmd, cwd, timeout=300):
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return result.stdout, result.stderr, result.returncode

SEVERITY_MAP = {
    'CRITICAL': 'CRITICAL',
    'HIGH': 'HIGH',
    'ERROR': 'HIGH',
    'MEDIUM': 'MEDIUM',
    'WARNING': 'MEDIUM',
    'LOW': 'LOW',
    'NOTE': 'LOW',
    'INFO': 'INFO',
    'INFORMATIONAL': 'INFO',
}

def normalize_severity(raw: str) -> str:
    return SEVERITY_MAP.get((raw or '').upper(), 'INFO')

