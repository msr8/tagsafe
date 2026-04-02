from app.consts     import GITHUB_APP_NAME, GITHUB_CLIENT_ID, GITHUB_KEY_PATH
from app.utils      import login_required, get_installation_token
from app.models     import Installation, Commit, PullRequest
from app.extensions import db
from app.scanners   import pr_scan, commit_scan
from loguru         import logger

from flask import Blueprint, app, render_template, session, redirect, url_for, flash, request, send_from_directory, jsonify
from flask_restful import Resource

from json import dumps
import requests as rq
from rich import inspect
import datetime as dt
from collections import defaultdict
import tempfile
from git import Repo



webhook_bp = Blueprint('webhook', __name__)



@webhook_bp.route('/webhook', methods=['POST'])
def github_webhook():
    event_type = request.headers.get('X-GitHub-Event')
    payload    = request.json
    # inspect(payload)
    # with open('test.json', 'w') as f:
    #     f.write(dumps(payload, indent=4))

    if event_type == 'ping':
        logger.info('Webhook connected successfully!')
        return jsonify({'status': 'ping received'}), 200
    

    if event_type == 'installation':
        if payload.get('action') == 'created':
            if db.session.get(Installation, payload['installation']['id']): return jsonify({'status': 'installation already exists'}), 200
            obj = Installation(
                installation_id = payload['installation']['id'],
                issuer_username = payload['sender']['login'],
                issuer_pfp_url  = payload['sender']['avatar_url'],
                repos           = payload['repositories'],
                user_id         = payload['installation']['account']['id']
            )
            db.session.add(obj)
            db.session.commit()
        
        elif payload.get('action') == 'suspended':
            obj = db.session.get(Installation, payload['installation']['id'])
            if obj:
                obj.is_active = False
                db.session.commit()

        elif payload.get('action') == 'unsuspended':
            obj = db.session.get(Installation, payload['installation']['id'])
            if obj:
                obj.is_active = True
                db.session.commit()

        elif payload.get('action') == 'deleted':
            obj = db.session.get(Installation, payload['installation']['id'])
            if obj:
                db.session.delete(obj)
                db.session.commit()


    # Added or removed repos
    elif event_type == 'installation_repositories':
        installation_id   = payload['installation']['id']
        obj               = db.session.get(Installation, installation_id)
        existing_repo_ids = {repo['id'] for repo in obj.repos}
        
        # The added repos
        for repo in payload.get('repositories_added', []):
            if repo['id'] not in existing_repo_ids: obj.repos.append(repo)
        # The removed repos
        removed_repo_ids = {repo['id'] for repo in payload.get('repositories_removed', [])}
        obj.repos = [r for r in obj.repos if r['id'] not in removed_repo_ids]

        # obj.last_repos_update = db.func.now()
        db.session.commit()


    # Code Push (Commit)
    elif event_type == 'push':
        # Find out which installation triggered this
        installation_id = payload['installation']['id']
        repo_name       = payload['repository']['full_name']
        pusher          = payload['pusher']['name']
        
        logger.info(f'[!] ALERT: {pusher} just pushed code to {repo_name}')
        
        # Get our bot's master key for this repo
        token = get_installation_token(installation_id)
        logger.info('Token acquired! Fetching commit details...')
        
        # Get the commits URL
        commits_url = payload['repository']['commits_url'].replace('{/sha}', '')
        # Get the commits info from github
        auth_headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        commits_json = rq.get(commits_url, headers=auth_headers)
        inspect(commits_json)
        with open('temp.json', 'w') as f:
            f.write(dumps(commits_json.json(), indent=4))
        
        latest_commit_msg = commits_json.json()[0]['commit']['message']
        logger.success(f'SUCCESS! Latest commit message: "{latest_commit_msg}"')
        commit_objs = []
        for commit in commits_json.json():
            # If this commit is already present in our DB, we can skip it
            if db.session.get(Commit, commit['sha']): continue
            logger.info(f'Processing commit "{commit["commit"]["message"]}" - {commit["sha"]}')
            commit_obj = Commit(
                sha             = commit['sha'],
                repo_id         = payload['repository']['id'], # Since repo id is not present in `commit`
                author_email    = commit['commit']['author']['email'],
                author_name     = commit['commit']['author']['name'],
                author_username = commit['author']['login'] if commit.get('author') else None,
                message         = commit['commit']['message'],
                url             = commit['html_url'],
                timestamp       = dt.datetime.strptime(commit['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ'),
                installation_id = installation_id
            )
            commit_objs.append(commit_obj)
        # Do to_scan=True for the latest commit
        commit_objs[0].to_scan = True
        # Reverse the list so that the oldest commit gets added first
        commit_objs.reverse()
        # db.session.add_all(commit_objs)
        # db.session.commit()

        commit = commit_objs[-1]
        commit_scan(commit, token, payload)

            # # -----> Scanning stuff <-----
            # # Looping through the commits from latest to oldest to get the LISTS of commits which changed stuff
            # to_check_commits = []
            # for idx,commit in enumerate(commits_json.json()):
            #     # Stop the loop when we reach the last commit which we scanned
            #     commit_i = db.session.get(Commit, commit['sha'])
            #     if commit['sha'] != latest_commit_sha and commit_i.to_scan: break
            #     to_check_commits.append(commit)
            
            # # Now go through the oldest to latest commits to get the changed files
            # changed_files = defaultdict(dict)
            # for commit in reversed(to_check_commits):
            #     commit_url = commit['url'] # API URL to get the commit details, including the changed files
            #     commit_details = rq.get(commit_url, headers=auth_headers).json()
            #     # if not commit_details.ok: files = commit_details.json().get('files', [])
            #     files = commit_details['files']
            #     for file in files:
            #         fn = file['filename']
            #         if file['status'] != 'removed': # We don't need to scan deleted files
            #             if fn in changed_files: del changed_files[fn]
            #         if file['status'] == 'added':
            #             changed_files[fn] = file
            #         if file['status'] == 'modified':
            #             changed_files[fn] = file

                
        return jsonify({'status': 'push processed'}), 200
    

    # Pull Request
    elif event_type == 'pull_request':
        if not payload.get('action') in ['opened', 'synchronize']: 
            logger.debug(f'Ignored PR action: {payload.get("action")}')
            return jsonify({'status': 'ignored action'}), 200
        with open('pr_payload.json', 'w') as f:
            f.write(dumps(payload, indent=4))
        
        logger.info(f'[!] ALERT: PR #{payload["number"]} was {payload["action"]} in {payload["repository"]["full_name"]}')

        # If new PR, make a new PR object in our DB
        # if payload['action'] == 'opened':
        pr_obj = db.session.get(PullRequest, payload['pull_request']['id'])
        if not pr_obj:
            pr_obj = PullRequest(
                pr_id           = payload['pull_request']['id'],
                repo_id         = payload['repository']['id'], # Since repo id is not present in `pull_request`
                author_email    = payload['pull_request']['user']['email'] if payload['pull_request']['user'].get('email') else None,
                author_name     = payload['pull_request']['user']['name']  if payload['pull_request']['user'].get('name') else None,
                author_username = payload['pull_request']['user']['login'],
                title           = payload['pull_request']['title'],
                description     = payload['pull_request']['body'],
                html_url        = payload['pull_request']['html_url'],
                api_url         = payload['pull_request']['url'],
                timestamp       = dt.datetime.strptime(payload['pull_request']['created_at'], '%Y-%m-%dT%H:%M:%SZ'),
                installation_id = payload['installation']['id']
            )
            db.session.add(pr_obj)
            db.session.commit()

        # Run the scanner on this PR
        token = get_installation_token(payload['installation']['id'])
        pr_scan(pr_obj, token, payload)


    return jsonify({'status': 'ignored'}), 200
    

