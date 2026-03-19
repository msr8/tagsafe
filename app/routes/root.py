from app.consts import GITHUB_APP_NAME
from app.utils  import login_required

from flask import Blueprint, render_template, session, redirect, url_for, flash, request, send_from_directory
from flask_restful import Resource

from json import dumps



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
    return render_template('dashboard.html', github_app_name=GITHUB_APP_NAME)




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
    



