"""
Scanner service: clones the repository at the target commit, detects language,
runs the appropriate static-analysis tools, parses their JSON output, and
persists Finding records to the database.

Supported tools:
  - Python  → bandit
  - Go      → gosec
  - JS/TS   → nodejsscan
  - C/C++   → cppcheck
  - Any     → semgrep (community rules)
"""

import os
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from backend.app import db
from backend.models.models import Finding

# ── helpers ───────────────────────────────────────────────────────────────────

SEVERITY_MAP = {
    "CRITICAL": "CRITICAL",
    "HIGH": "HIGH",
    "ERROR": "HIGH",
    "MEDIUM": "MEDIUM",
    "WARNING": "MEDIUM",
    "LOW": "LOW",
    "NOTE": "LOW",
    "INFO": "INFO",
    "INFORMATIONAL": "INFO",
}


def _normalize_severity(raw: str) -> str:
    return SEVERITY_MAP.get((raw or "").upper(), "INFO")


def _run(cmd, cwd, timeout=300):
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )
    return result.stdout, result.stderr, result.returncode


# ── clone ─────────────────────────────────────────────────────────────────────

def _clone_repo(repo_full_name: str, commit_sha: str, token: str, dest: str):
    url = f"https://x-access-token:{token}@github.com/{repo_full_name}.git"
    _run(["git", "clone", "--depth", "50", url, dest], cwd="/tmp")
    _run(["git", "checkout", commit_sha], cwd=dest)


# ── language detection ────────────────────────────────────────────────────────

def _detect_languages(repo_path: str) -> set:
    langs = set()
    for p in Path(repo_path).rglob("*"):
        if p.is_file():
            suffix = p.suffix.lower()
            if suffix == ".py":
                langs.add("python")
            elif suffix == ".go":
                langs.add("go")
            elif suffix in (".js", ".ts", ".jsx", ".tsx"):
                langs.add("javascript")
            elif suffix in (".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"):
                langs.add("cpp")
    return langs


# ── tool runners ──────────────────────────────────────────────────────────────

def _run_bandit(repo_path: str, scan_id: int) -> list[Finding]:
    findings = []
    out, _, _ = _run(
        ["bandit", "-r", ".", "-f", "json", "-q"],
        cwd=repo_path,
    )
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return findings

    for result in data.get("results", []):
        f = Finding(
            scan_run_id=scan_id,
            tool="bandit",
            rule_id=result.get("test_id"),
            severity=_normalize_severity(result.get("issue_severity", "")),
            confidence=result.get("issue_confidence", ""),
            file_path=result.get("filename", "").replace(repo_path, "").lstrip("/"),
            line_start=result.get("line_number"),
            line_end=result.get("line_range", [None])[-1],
            message=result.get("issue_text", ""),
            code_snippet=result.get("code", ""),
            cwe=result.get("issue_cwe", {}).get("id", ""),
        )
        findings.append(f)
    return findings


def _run_gosec(repo_path: str, scan_id: int) -> list[Finding]:
    findings = []
    out, _, _ = _run(
        ["gosec", "-fmt=json", "-quiet", "./..."],
        cwd=repo_path,
    )
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return findings

    for issue in data.get("Issues", []):
        f = Finding(
            scan_run_id=scan_id,
            tool="gosec",
            rule_id=issue.get("rule_id"),
            severity=_normalize_severity(issue.get("severity", "")),
            confidence=issue.get("confidence", ""),
            file_path=issue.get("file", "").replace(repo_path, "").lstrip("/"),
            line_start=int(issue.get("line", 0) or 0),
            message=issue.get("details", ""),
            cwe=issue.get("cwe", {}).get("id", ""),
        )
        findings.append(f)
    return findings


def _run_nodejsscan(repo_path: str, scan_id: int) -> list[Finding]:
    findings = []
    out, _, _ = _run(
        ["nodejsscan", "-d", ".", "-o", "/tmp/nodejsscan_out.json"],
        cwd=repo_path,
    )
    try:
        with open("/tmp/nodejsscan_out.json") as fh:
            data = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return findings

    for severity_key in ("nodejs_issues", "template_injection", "misc_issues"):
        for title, issues in (data.get(severity_key) or {}).items():
            for issue in (issues if isinstance(issues, list) else [issues]):
                f = Finding(
                    scan_run_id=scan_id,
                    tool="nodejsscan",
                    rule_id=title,
                    severity=_normalize_severity(issue.get("level", "MEDIUM")),
                    file_path=issue.get("filename", "").replace(repo_path, "").lstrip("/"),
                    line_start=issue.get("line"),
                    message=issue.get("description", title),
                    code_snippet=issue.get("lines", ""),
                    owasp=issue.get("tag", ""),
                )
                findings.append(f)
    return findings


def _run_cppcheck(repo_path: str, scan_id: int) -> list[Finding]:
    findings = []
    out, _, _ = _run(
        ["cppcheck", "--enable=all", "--output-file=/tmp/cppcheck_out.xml",
         "--xml", "--xml-version=2", "."],
        cwd=repo_path,
    )
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse("/tmp/cppcheck_out.xml")
        root = tree.getroot()
    except Exception:
        return findings

    for error in root.iter("error"):
        loc = error.find("location")
        severity_raw = error.get("severity", "information")
        severity_map = {
            "error": "HIGH", "warning": "MEDIUM",
            "style": "LOW", "performance": "LOW",
            "portability": "LOW", "information": "INFO",
        }
        f = Finding(
            scan_run_id=scan_id,
            tool="cppcheck",
            rule_id=error.get("id"),
            severity=severity_map.get(severity_raw, "INFO"),
            file_path=(loc.get("file", "") if loc is not None else "").replace(repo_path, "").lstrip("/"),
            line_start=int(loc.get("line", 0)) if loc is not None else None,
            message=error.get("msg", ""),
            code_snippet=error.get("verbose", ""),
        )
        findings.append(f)
    return findings


def _run_semgrep(repo_path: str, scan_id: int) -> list[Finding]:
    findings = []
    out, _, _ = _run(
        ["semgrep", "--config=auto", "--json", "--quiet", "."],
        cwd=repo_path,
        timeout=600,
    )
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return findings

    for result in data.get("results", []):
        meta = result.get("extra", {}).get("metadata", {})
        f = Finding(
            scan_run_id=scan_id,
            tool="semgrep",
            rule_id=result.get("check_id", ""),
            severity=_normalize_severity(result.get("extra", {}).get("severity", "")),
            file_path=result.get("path", "").replace(repo_path, "").lstrip("/"),
            line_start=result.get("start", {}).get("line"),
            line_end=result.get("end", {}).get("line"),
            message=result.get("extra", {}).get("message", ""),
            code_snippet=result.get("extra", {}).get("lines", ""),
            cwe=",".join(meta.get("cwe", [])) if isinstance(meta.get("cwe"), list) else meta.get("cwe", ""),
            owasp=",".join(meta.get("owasp", [])) if isinstance(meta.get("owasp"), list) else meta.get("owasp", ""),
        )
        findings.append(f)
    return findings


# ── main pipeline ─────────────────────────────────────────────────────────────

def run_scan_pipeline(repo_full_name: str, commit_sha: str, access_token: str, scan_id: int):
    work_dir = tempfile.mkdtemp(prefix="secureguard_")
    repo_path = os.path.join(work_dir, "repo")
    all_findings = []

    try:
        _clone_repo(repo_full_name, commit_sha, access_token, repo_path)
        langs = _detect_languages(repo_path)

        runners = [_run_semgrep]   # always run semgrep

        if "python" in langs:
            runners.append(_run_bandit)
        if "go" in langs:
            runners.append(_run_gosec)
        if "javascript" in langs:
            runners.append(_run_nodejsscan)
        if "cpp" in langs:
            runners.append(_run_cppcheck)

        for runner in runners:
            try:
                findings = runner(repo_path, scan_id)
                all_findings.extend(findings)
            except Exception:
                pass  # one tool failing shouldn't kill the whole scan

        # Persist
        for f in all_findings:
            db.session.add(f)
        db.session.commit()

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    counts = {"total": len(all_findings)}
    for f in all_findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    return all_findings, counts