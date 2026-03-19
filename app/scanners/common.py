import subprocess
import sys

def run_cmd(cmd, cwd, timeout=300):
    result = subprocess.run(
        cmd,
        cwd     = cwd,
        capture_output = True,
        text    = True,
        timeout = timeout,
        # # Do not display the output of the command
        # stderr   = subprocess.PIPE,
        # stdout   = subprocess.PIPE,
    )
    return result.stdout, result.stderr, result.returncode

SEVERITY_MAP = {
    'critical':      'CRITICAL',
    'high':          'HIGH',
    'error':         'HIGH',
    'medium':        'MEDIUM',
    'warn':          'WARNING',
    'warning':       'WARNING',
    'low':           'LOW',
    'note':          'LOW',
    'info':          'INFO',
    'informational': 'INFO',
}

def normalize_severity(raw: str) -> str:
    return SEVERITY_MAP.get((raw or '').lower(), 'INFO')

