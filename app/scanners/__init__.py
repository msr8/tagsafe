from app.extensions import db
from app.models     import *

from . import all_semgrep, c_cppcheck, go_gosec, js_nodejsscan, py_bandit

from git import Repo
import tempfile
import os

# SCANNERS = {
#     'all': all_semgrep,
#     'c':   c_cppcheck,
#     'cpp': c_cppcheck,
# }


def scan(commit:Commit, token:str, payload:dict):
    # Clone this repo
    with tempfile.TemporaryDirectory() as tmpdir:
        auth_url = f'https://x-access-token:{token}@github.com/{payload["repository"]["full_name"]}.git'
        print(f'Cloning the repo from {auth_url} ...')
        repo = Repo.clone_from(auth_url, 'repo', env={'GIT_TERMINAL_PROMPT': '0'})
        # Checkout to the commit that triggered the webhook
        repo.git.checkout(commit.sha)
        print(f'Checked out to commit {commit.sha}. Repo is ready for scanning!')

        # Go through all the files and see what extentions are present, and run the respective scanners
        scanners = {'semgrep'} 
        for root, dirs, files in os.walk('repo'):
            for file in files:
                ext = file.split('.')[-1]
                if   ext in ['c', 'cpp', 'h', 'hpp']: scanners.add('c_cppcheck')
                elif ext in ['go']: scanners.add('go_gosec')
                elif ext in ['js']: scanners.add('js_nodejsscan')
                elif ext in ['py']: scanners.add('py_bandit')
        
        print(f'Scanners to run based on file extensions: {scanners}')
        if 'all_semgrep'   in scanners: all_semgrep.run  ('repo', commit.sha)
        if 'c_cppcheck'    in scanners: c_cppcheck.run   ('repo', commit.sha)
        if 'go_gosec'      in scanners: go_gosec.run     ('repo', commit.sha)
        if 'js_nodejsscan' in scanners: js_nodejsscan.run('repo', commit.sha)
        if 'py_bandit'     in scanners: py_bandit.run    ('repo', commit.sha)

        commit.to_scan = False
        commit.fully_scanned = True
        db.session.commit()
