from app.consts     import *
from app.models     import *
from app.extensions import db

from flask import request, session, redirect, url_for, flash, get_flashed_messages

from functools import wraps
from re import match



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
