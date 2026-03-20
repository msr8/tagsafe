from app.consts     import *
from app.models     import *
from app.extensions import db

from flask import request, session, redirect, url_for, flash, get_flashed_messages

from functools import wraps
from re import match
import time
import jwt
import requests as rq



# Wrapper for login required but it also takes in a boolean indicating wether to return the data as json or not
def login_required(json=False):
    def wrapper(f):
        @wraps(f)
        def inner(*args, **kwargs):
            if not session.get('logged_in'):
                flash('You must be logged in to access this resource', 'error')
                # redirect_to = f.__module__.split('.')[-1] + '.' + f.__name__
                redirect_to = request.url
                session['redirect_to'] = redirect_to

                if not json: return redirect(url_for(LOGIN_FAIL_REDIRECT))
                return {'message': 'You are not logged in', 'status': 'error'}, 401
            
            return f(*args, **kwargs)
        
        return inner
    return wrapper




def check_email(to_check:str) -> bool:
    return bool(match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', to_check))




def check_google_signup(email:str) -> bool:
    user = db.session.get(User, session['email'])    
    return user and (user.password is None)


def get_installation_token(installation_id):
    '''Generates a fresh token for the specific repo that triggered the webhook'''
    with open(GITHUB_KEY_PATH, 'rb') as key_file:
        private_key = key_file.read()

    payload = {
        'iat': int(time.time()) - 60,
        'exp': int(time.time()) + (60 * 10),
        'iss': GITHUB_CLIENT_ID
    }
    
    encoded_jwt = jwt.encode(payload, private_key, algorithm='RS256')
    url = f'https://api.github.com/app/installations/{installation_id}/access_tokens'
    
    headers = {
        'Authorization': f'Bearer {encoded_jwt}',
        'Accept': 'application/vnd.github.v3+json'
    }

    resp = rq.post(url, headers=headers)
    if not resp.ok:
        print(f'Token error: {resp.text}')
        return None
    return resp.json()['token']