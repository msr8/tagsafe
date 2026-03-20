from app.consts     import GITHUB_APP_NAME, GITHUB_CLIENT_ID, GITHUB_KEY_PATH
from app.utils      import login_required, get_installation_token
from app.models     import Installation
from app.extensions import db

from flask import Blueprint, app, render_template, session, redirect, url_for, flash, request, send_from_directory, jsonify
from flask_restful import Resource

from json import dumps
import requests as rq
from rich import inspect



root_bp = Blueprint('root', __name__)


# Favicon (https://tedboy.github.io/flask/patterns/favicon.html)
@root_bp.route('/favicon.ico')
def page_favicon():
    return send_from_directory('static', 'favicon-128.ico', mimetype='image/vnd.microsoft.icon')




@root_bp.route('/')
def page_index():
    return render_template('index.html')



@root_bp.route('/dashboard')
@login_required() # ALWAYS remember to keep login_required() below the route decorator, otherwise it will not work (idfk why)
def page_dashboard():
    # # Get authorised repos for this user
    # installations = db.session.query(Installation).filter_by(issuer_username=session['username']).all()
    # repos = []
    # for inst in installations:
    #     if not inst.is_active: continue
    #     token = get_installation_token(inst.installation_id)
    #     if token:
    #         auth_headers = {
    #             'Authorization': f'Bearer {token}',
    #             'Accept': 'application/vnd.github.v3+json'
    #         }
    #         repos_resp = rq.get(f'https://api.github.com/installation/repositories', headers=auth_headers)
    #         inspect(repos_resp)
    #         if repos_resp.ok:
    #             repos.extend([ i['full_name'] for i in repos_resp.json().get('repositories', []) ])
    
    # Get all repos from all installations of this user
    installations = db.session.query(Installation).filter_by(issuer_username=session['username']).all()
    # repos = [ r['full_name'] for inst in installations if inst.is_active for r in inst.repos ]
    repos = []
    for inst in installations:
        if not inst.is_active: continue
        for r in inst.repos: repos.append(r['full_name'])
    return render_template('dashboard.html', github_app_name=GITHUB_APP_NAME, repos=repos)




@root_bp.route('/webhook', methods=['POST'])
def github_webhook():
    event_type = request.headers.get('X-GitHub-Event')
    payload    = request.json
    inspect(payload)
    with open('test.json', 'w') as f:
        f.write(dumps(payload, indent=4))

    if event_type == 'ping':
        print('Webhook connected successfully!')
        return jsonify({'status': 'ping received'}), 200
    

    if event_type == 'installation':
        if payload.get('action') == 'created':
            obj = Installation(
                installation_id = payload['installation']['id'],
                issuer_username = payload['sender']['login'],
                issuer_pfp      = payload['sender']['avatar_url'],
                repos           = payload['repositories']
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
        # 1. Find out which installation triggered this
        installation_id = payload['installation']['id']
        repo_name       = payload['repository']['full_name']
        pusher          = payload['pusher']['name']
        
        print(f'\n[!] ALERT: {pusher} just pushed code to {repo_name}')
        
        # 2. Get our bot's master key for this repo
        print('Generating access token...')
        token = get_installation_token(installation_id)
        
        if not token: return jsonify({'status': 'token acquisition failed'}), 500
        if token:
            print('Token acquired! Fetching commit details...')
            # 3. Prove we can read the code by hitting the API
            commits_url = payload['repository']['commits_url'].replace('{/sha}', '')
            auth_headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            repo_resp = rq.get(commits_url, headers=auth_headers)
            if repo_resp.ok:
                latest_commit = repo_resp.json()[0]['commit']['message']
                print(f'SUCCESS! Latest commit message: "{latest_commit}"')
                
                # ---> THIS IS WHERE YOUR SAST SCRIPT WILL GO <---
                
        return jsonify({'status': 'push processed'}), 200
    

    # Pull Request
    elif event_type == 'pull_request':
        action = payload.get('action')
        
        # We only want to run analysis when new code is introduced
        if action in ['opened', 'synchronize']:
            installation_id = payload['installation']['id']
            repo_owner = payload['repository']['owner']['login']
            repo_name = payload['repository']['name']
            pr_number = payload['pull_request']['number']
            
            print(f'\n[!] ALERT: PR #{pr_number} was {action} in {repo_owner}/{repo_name}')
            
            # 1. Wake up the bot and get the token
            print('Generating access token...')
            token = get_installation_token(installation_id)
            
            if token:
                # 2. Ask GitHub for the list of files changed in this specific PR
                files_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files'
                auth_headers = {
                    'Authorization': f'Bearer {token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
                
                files_resp = rq.get(files_url, headers=auth_headers)
                
                if files_resp.ok:
                    changed_files = files_resp.json()
                    print(f'SUCCESS! Found {len(changed_files)} changed files to analyze.')
                    
                    # 3. Loop through the files to get the code
                    for file in changed_files:
                        filename = file['filename']
                        status = file['status'] # e.g., 'added', 'modified', 'removed'
                        
                        # We don't need to scan deleted files
                        if status != 'removed':
                            # 'raw_url' gives you the direct link to download the full, updated file text
                            raw_file_url = file.get('raw_url')
                            print(f' - Fetching and scanning: {filename}')
                            
                            # ---> YOUR SAST ENGINE GOES HERE <---
                            # You would do: raw_code = rq.get(raw_file_url, headers=auth_headers).text
                            # And then pass 'raw_code' into your security analysis script.
                            
                else:
                    print(f'Failed to fetch PR files: {files_resp.text}')
                    
            return jsonify({'status': 'pr processed'}), 200
            
        else:
            # We ignore things like 'labeled', 'closed', 'assigned'
            print(f'Ignored PR action: {action}')
            return jsonify({'status': 'ignored action'}), 200

    return jsonify({'status': 'ignored'}), 200
    


class TestAPI(Resource):
    def get(self):
        # Return all the arguments passed in the URL
        return request.args

    def post(self):
        # Return all the arguments passed in the request form & body
        form_args = request.form
        json_args = request.get_json()

        return {'form': form_args, 'json': json_args}




@root_bp.route('/session')
def page_session():
    # TypeError: Object of type SqlAlchemySession is not JSON serializable
    return f'<pre>{dumps(dict(session), indent=4)}</pre>'
    # print(session.keys())
    # print(session['logged_in    '])
    # return str(session)
    



