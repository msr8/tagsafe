from app.models     import *
from app.consts     import *
from app.utils      import login_required, check_email, check_google_signup
from app.extensions import db

from flask import Blueprint, redirect, url_for, session, render_template, request, flash
from flask_restful import Resource
from flask_dance.contrib.google import google
from flask_dance.contrib.github import github
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError

from bcrypt import hashpw, gensalt, checkpw
import rich

auth_bp = Blueprint('auth', __name__)






@auth_bp.route('/github-authorised/')
def page_github_authorised():
    # Get the info
    try: resp = github.get('/user')
    except TokenExpiredError:
        flash('Your session has expired, please login again', 'warning')
        session.clear()
        return redirect(url_for('root.page_index'))
    except:
        session.clear()
        return 'Internal Server Error', 500
    if not resp.ok:
        session.clear()
        return f'Failed to fetch user info, please <a href="{url_for("root.page_index")}">login again</a>', 500
    resp:dict = resp.json()

    session['logged_in'] = True
    session['username']  = resp['login']
    session['pfp_url']   = resp['avatar_url']
    session['user_id']   = resp['id']

    # rich.inspect(resp, all=True)
    with open('after-authorisation.json', 'w') as f:
        import json
        json.dump(resp, f, indent=4)
    if not db.session.get(User, resp['id']):
        user = User(user_id=resp['id'], username=resp['login'], pfp_url=resp['avatar_url'])
        db.session.add(user)
        db.session.commit()

    # return resp
    return redirect( session.pop('redirect_to', url_for(POST_LOGIN_REDIRECT)) )



# @auth_bp.route('/google-authorised/')
# def page_google_authorised():
#     # Get his info
#     try: resp:Response = google.get('/oauth2/v1/userinfo')
#     except TokenExpiredError: return redirect(url_for('auth.page_login'))
#     except: return 'Internal Server Error', 500
#     # Check if the responses are valid
#     if not resp.ok:                    return f'Failed to fetch user info, please <a href="{url_for("auth.page_login")}">login again</a>', 500
#     resp:dict = resp.json()
#     if not resp.get('verified_email'): return 'Email not verified', 403
#     if not resp.get('email'):          return 'Unable to fetch email', 500
    
#     email = resp['email']
#     user  = db.session.get(User, email)

#     # If we have never seen this user before, add him to the database
#     if not user:
#         username = email.split('@')[0]
#         user = User(email=resp['email'], username=resp['email'].split('@')[0])
#         db.session.add(user)
#         db.session.add(Usernames(username=username, email=email))
#         db.session.commit()
#     else:
#         username = user.username
#     # Save the user's info in the session
#     session['logged_in']            = True
#     session['email']                = email
#     session['username']             = username
#     session['signed_up_via_google'] = user.password is None

#     return redirect( session.pop('redirect_to', url_for(POST_LOGIN_REDIRECT)) )





@auth_bp.route('/logout/')
@login_required()
def page_logout():
    session.clear()
    return redirect(url_for(POST_LOGOUT_REDIRECT))
    # return f'Successfully logged out. You may now return to the <a href="{url_for("root.page_index")}">homepage</a>'









