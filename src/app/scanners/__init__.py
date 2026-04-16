from rich import inspect

from app.extensions import db
from app.models     import *

from . import all_semgrep, c_cppcheck, go_gosec, js_nodejsscan, py_bandit, ruby_brakeman, rust_cargoaudit, all_trivy, all_dependencycheck, all_gitleaks, py_safety, all_yara

from git import Repo
from loguru import logger
import requests as rq
import datetime as dt

import tempfile
import os
import pathlib

# SCANNERS = {
#     'all': all_semgrep,
#     'c':   c_cppcheck,
#     'cpp': c_cppcheck,
# }


def commit_scan(commit:Commit, token:str, payload:dict) -> tuple[set, list[Finding]]:
    # Clone this repo
    with tempfile.TemporaryDirectory() as tmpdir:
        # tmpdir = 'repo2'
        auth_url = f'https://x-access-token:{token}@github.com/{payload["repository"]["full_name"]}.git'
        logger.opt(colors=True).info(f'Cloning the repo from <magenta>{auth_url}</> in <magenta>{tmpdir}</> ...')
        repo = Repo.clone_from(auth_url, tmpdir, env={'GIT_TERMINAL_PROMPT': '0'})
        # Checkout to the commit that triggered the webhook
        repo.git.checkout(commit.sha)
        logger.opt(colors=True).info(f'Checked out to commit <magenta>{commit.sha}</magenta>. Repo is ready for scanning!')

        # Go through all the files and see what extentions are present, and run the respective scanners
        scanners = {'semgrep', 'all_trivy', 'all_dependencycheck', 'all_gitleaks', 'all_yara'} 
        for root, dirs, files in os.walk(tmpdir):
            for file in files:
                ext = file.split('.')[-1]
                # logger.debug(f'Found file: {file} with extension: {ext}')
                if   ext in ['c', 'cpp', 'h', 'hpp']: scanners.add('c_cppcheck')
                elif ext in ['go']: scanners.add('go_gosec')
                elif ext in ['js']: scanners.add('js_nodejsscan')
                elif ext in ['py']: scanners.add('py_bandit')
                elif ext in ['rb']: scanners.add('ruby_brakeman')
                if file == 'Cargo.lock': scanners.add('rust_cargoaudit')
                # Removed this cause safety requires an acc :(
                # if file == 'requirements.txt': scanners.add('py_safety')
        
        logger.opt(colors=True).info(f'Scanners to run based on file extensions: <magenta>{scanners}</magenta>')
        findings = []
        if 'all_semgrep'         in scanners: findings.extend(all_semgrep.run         (tmpdir))
        if 'all_yara'            in scanners: findings.extend(all_yara.run            (tmpdir))
        if 'all_trivy'           in scanners: findings.extend(all_trivy.run           (tmpdir))
        # if 'all_dependencycheck' in scanners: findings.extend(all_dependencycheck.run (tmpdir))
        if 'all_gitleaks'        in scanners: findings.extend(all_gitleaks.run        (tmpdir))
        if 'c_cppcheck'          in scanners: findings.extend(c_cppcheck.run          (tmpdir))
        if 'go_gosec'            in scanners: findings.extend(go_gosec.run            (tmpdir))
        if 'js_nodejsscan'       in scanners: findings.extend(js_nodejsscan.run       (tmpdir))
        if 'py_bandit'           in scanners: findings.extend(py_bandit.run           (tmpdir))
        if 'py_safety'           in scanners: findings.extend(py_safety.run           (tmpdir))
        if 'ruby_brakeman'       in scanners: findings.extend(ruby_brakeman.run       (tmpdir))
        if 'rust_cargoaudit'     in scanners: findings.extend(rust_cargoaudit.run     (tmpdir))

        commit.to_scan       = False
        commit.fully_scanned = True
        for f in findings: f.commit_sha = commit.sha
        db.session.add_all(findings)
        db.session.commit()

    return scanners, findings



def pr_scan(pr:PullRequest, token:str, payload:dict) -> tuple[set, list[Finding]]:
    # For PRs, we only want to scan the changed files, so we will not clone the entire repo, but instead use GitHub's API to get the changed files and their contents, and then run the scanners on those files.

    # Get changed files in this PR using GitHub API
    auth_headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    files_resp = rq.get(pr.api_url + '/files', headers=auth_headers)

    scanners = {'semgrep', 'all_trivy', 'all_dependencycheck', 'all_gitleaks', 'all_yara'}
    # Download the changed files
    with tempfile.TemporaryDirectory() as tmpdir:
        # tmpdir = 'repo'
        for file in files_resp.json():
            if file['status'] == 'removed': continue
            file_path = file['filename']
            raw_url   = file['contents_url']
            # Save this file in the temp directory, maintaining the directory structure
            full_path = os.path.join(tmpdir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            raw_headers = auth_headers.copy()
            raw_headers['Accept'] = 'application/vnd.github.v3.raw' # To get the raw file. Otherwise, auth headers are ingored and we get a 404 on redirect
            with open(full_path, 'w', encoding='utf-8') as f:
                resp = rq.get(raw_url, headers=raw_headers)
                f.write(resp.text)
            # Determine which scanners to run based on file extension
            ext = file_path.split('.')[-1]
            print(ext)
            if  ext in ['c', 'cpp', 'h', 'hpp']: scanners.add('c_cppcheck')
            elif ext in ['go']: scanners.add('go_gosec')
            elif ext in ['js']: scanners.add('js_nodejsscan')
            elif ext in ['py']: scanners.add('py_bandit')
            elif ext in ['rb']: scanners.add('ruby_brakeman')
            if file_path.endswith('Cargo.lock'): scanners.add('rust_cargoaudit')
            if file_path.endswith('requirements.txt'): scanners.add('py_safety')
    
        logger.opt(colors=True).info(f'Downloaded changed files for PR #{pr.pr_id} in <magenta>{tmpdir}</> | <magenta>{scanners}</>')
        findings = []
        if 'all_semgrep'         in scanners: findings.extend(all_semgrep.run         (tmpdir))
        if 'all_yara'            in scanners: findings.extend(all_yara.run            (tmpdir))
        if 'all_trivy'           in scanners: findings.extend(all_trivy.run           (tmpdir))
        if 'all_dependencycheck' in scanners: findings.extend(all_dependencycheck.run (tmpdir))
        if 'all_gitleaks'        in scanners: findings.extend(all_gitleaks.run        (tmpdir))
        if 'c_cppcheck'          in scanners: findings.extend(c_cppcheck.run          (tmpdir))
        if 'go_gosec'            in scanners: findings.extend(go_gosec.run            (tmpdir))
        if 'js_nodejsscan'       in scanners: findings.extend(js_nodejsscan.run       (tmpdir))
        if 'py_bandit'           in scanners: findings.extend(py_bandit.run           (tmpdir))
        if 'py_safety'           in scanners: findings.extend(py_safety.run           (tmpdir))
        if 'ruby_brakeman'       in scanners: findings.extend(ruby_brakeman.run       (tmpdir))
        if 'rust_cargoaudit'     in scanners: findings.extend(rust_cargoaudit.run     (tmpdir))

    pr.fully_scanned = True
    for f in findings: f.pr_id = pr.pr_id
    db.session.add_all(findings)
    db.session.commit()

    with open('changed_files.json', 'w') as f:
        import json
        json.dump(files_resp.json(), f, indent=4)
    
    return scanners, findings
    

