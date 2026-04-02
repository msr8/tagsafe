from app.extensions import db
from app.models     import *

from . import all_semgrep, c_cppcheck, go_gosec, js_nodejsscan, py_bandit

from git import Repo
from loguru import logger
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
        # tmpdir = 'repo2'
        auth_url = f'https://x-access-token:{token}@github.com/{payload["repository"]["full_name"]}.git'
        logger.info(f'Cloning the repo from <bold>{auth_url}</bold> in <bold>{tmpdir}</bold> ...')
        repo = Repo.clone_from(auth_url, tmpdir, env={'GIT_TERMINAL_PROMPT': '0'})
        # Checkout to the commit that triggered the webhook
        repo.git.checkout(commit.sha)
        logger.info(f'Checked out to commit <bold>{commit.sha}</bold>. Repo is ready for scanning!')

        # Go through all the files and see what extentions are present, and run the respective scanners
        scanners = {'semgrep'} 
        for root, dirs, files in os.walk(tmpdir):
            for file in files:
                ext = file.split('.')[-1]
                logger.debug(f'Found file: {file} with extension: {ext}')
                if   ext in ['c', 'cpp', 'h', 'hpp']: scanners.add('c_cppcheck')
                elif ext in ['go']: scanners.add('go_gosec')
                elif ext in ['js']: scanners.add('js_nodejsscan')
                elif ext in ['py']: scanners.add('py_bandit')
        
        logger.info(f'Scanners to run based on file extensions: <bold>{scanners}</bold>')
        if 'all_semgrep'   in scanners: all_semgrep.run   (tmpdir, commit.sha)
        if 'c_cppcheck'    in scanners: c_cppcheck.run    (tmpdir, commit.sha)
        if 'go_gosec'      in scanners: go_gosec.run      (tmpdir, commit.sha)
        if 'js_nodejsscan' in scanners: js_nodejsscan.run (tmpdir, commit.sha)
        if 'py_bandit'     in scanners: py_bandit.run     (tmpdir, commit.sha)

        commit.to_scan = False
        commit.fully_scanned = True
        db.session.commit()
