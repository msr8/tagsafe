from flask import Flask, url_for
from flask_restful import Api
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.contrib.github import make_github_blueprint

from app.consts import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET
from app.routes import *
from app.extensions import db, sess
from app.config import Config

from sty import fg, bg, ef, rs

from os import environ


def create_app():
    print(ef.bold + fg.green + 'Creating app...' + rs.all)
    

    app = Flask(__name__)  
    api = Api(app)  
    # Load config
    # app.config.from_object('app.config.Config')
    app.config.from_object(Config)


    # Initialize extensions
    db.init_app(app)
    sess.init_app(app)
    with app.app_context(): db.create_all()
    

    # Google login
    environ['OAUTHLIB_RELAX_TOKEN_SCOPE']  = '1'
    environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # ONLY ON LOCAL ENV
    # google_bp = make_google_blueprint(
    #     client_id     = GOOGLE_CLIENT_ID,
    #     client_secret = GOOGLE_CLIENT_SECRET,
    #     scope = ['email'],
    #     offline = True,
    #     redirect_to = 'auth.page_google_authorised'
    # )
    # app.register_blueprint(google_bp, url_prefix='/login')
    github_blueprint = make_github_blueprint(
        client_id     = GITHUB_CLIENT_ID,
        client_secret = GITHUB_CLIENT_SECRET,
        # scope = 'repo',
        redirect_to = 'auth.page_github_authorised'
    )
    app.register_blueprint(github_blueprint, url_prefix='/github-login')
    

    # Register blueprints
    app.register_blueprint(root_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(webhook_bp)

    # Register API resources
    api.add_resource(TestAPI,           '/api/test')


    return app