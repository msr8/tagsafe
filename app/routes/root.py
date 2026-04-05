from app.consts     import GITHUB_APP_NAME, GITHUB_CLIENT_ID, GITHUB_KEY_PATH
from app.utils      import login_required, get_installation_token
from app.models     import Installation, Commit, User, PullRequest
from app.extensions import db

from flask import Blueprint, app, render_template, session, redirect, url_for, flash, request, send_from_directory, jsonify
from flask_restful import Resource

from json import dumps
import requests as rq
from rich import inspect
import datetime as dt
from collections import defaultdict
import tempfile
from git import Repo



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
    installations = db.session.get(User, session['user_id']).installations
    
    repos_data = []
    for inst in installations:
        if not inst.is_active: continue
        for r in inst.repos:
            repo_info = {
                'id': r.get('id'),
                'full_name': r.get('full_name'),
                'url': r.get('html_url'),
                'commits': []
            }
            # Fetch commits from DB for this repo (descending order by timestamp)
            commits = db.session.query(Commit).filter_by(repo_id=repo_info['id']).order_by(Commit.timestamp.desc()).all()
            for c in commits:
                repo_info['commits'].append({
                    'sha': c.sha,
                    'message': c.message,
                    'author': c.author_name,
                    'url': c.url,
                    'timestamp': c.timestamp.strftime("%b %d, %Y %I:%M %p"),
                    'findings': [f.to_dict() for f in c.findings]
                })
            
            repo_info['pull_requests'] = []
            prs = db.session.query(PullRequest).filter_by(repo_id=repo_info['id']).order_by(PullRequest.timestamp.desc()).all()
            for pr in prs:
                repo_info['pull_requests'].append({
                    'id': pr.pr_id,
                    'title': pr.title,
                    'author': pr.author_username or pr.author_name,
                    'url': pr.html_url,
                    'timestamp': pr.timestamp.strftime("%b %d, %Y %I:%M %p"),
                    'findings': [f.to_dict() for f in pr.findings]
                })
                
            repos_data.append(repo_info)
            
    user = db.session.get(User, session['user_id'])            
    return render_template('dashboard.html', github_app_name=GITHUB_APP_NAME, repos=repos_data, preference=user.preference or {})



@root_bp.route('/api/change-config', methods=['POST'])
def change_config():
    # See if the user is logged in
    if not session.get('logged_in'): return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    # Update the preference for this user in the database
    new_config      = request.get_json()
    user            = db.session.get(User, session['user_id'])

    if user.preference is None:
        user.preference = {}

    user.preference['email']              = new_config.get('email',              user.preference.get('email', ''))
    user.preference['severity_threshold'] = int(new_config.get('severity_threshold', user.preference.get('severity_threshold', 2)))
    
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Preferences saved successfully!'}), 200



@root_bp.route('/api/reload-repos', methods=['POST'])
def reload_repos():
    # See if the user is logged in
    if not session.get('logged_in'): return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    installations = db.session.get(User, session['user_id']).installations
    for inst in installations:
        if not inst.is_active: continue
        token = get_installation_token(inst.installation_id)
        if token:
            auth_headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            repos_resp = rq.get(f'https://api.github.com/installation/repositories', headers=auth_headers)
            inspect(repos_resp)
            if repos_resp.ok:
                inst.repos = repos_resp.json().get('repositories', [])
                db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Repos reloaded successfully'})




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
    



