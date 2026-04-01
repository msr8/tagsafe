from app.consts     import GITHUB_APP_NAME, GITHUB_CLIENT_ID, GITHUB_KEY_PATH
from app.utils      import login_required, get_installation_token
from app.models     import Installation, Commit
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
    installations = db.session.query(Installation).filter_by(issuer_username=session['username']).all()
    # repos = [ r['full_name'] for inst in installations if inst.is_active for r in inst.repos ]
    repos = []
    for inst in installations:
        if not inst.is_active: continue
        for r in inst.repos: repos.append(r['full_name'])
    return render_template('dashboard.html', github_app_name=GITHUB_APP_NAME, repos=repos)





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
    



