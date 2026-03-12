from app.models     import *
from app.consts     import *
from app.utils      import login_required, check_email, check_google_signup
from app.extensions import db

from flask import Blueprint, redirect, url_for, session, render_template, request
from flask_restful import Resource
from flask_dance.contrib.google import google
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError

from bcrypt import hashpw, gensalt, checkpw

auth_bp = Blueprint('auth', __name__)





@auth_bp.route('/login/')
def page_login():
    return render_template('auth/login.html')


@auth_bp.route('/signup')
def page_signup():
    return render_template('auth/signup.html')





class LoginAPI(Resource):
    def post(self):
        # # If the user is already logged in, redirect him to the user page
        # if session.get('logged_in'): return {'url': url_for('user.page_index'), 'status': 'redirect'}

        # Get data
        data              = request.get_json()
        email_or_username = data.get('email_or_username')
        password          = data.get('password')
        if not email_or_username: return {'message': 'Email or username not provided', 'status': 'error'}, 401
        if not password:          return {'message': 'Password not provided',          'status': 'error'}, 401

        # Check if we were provided the email or the username
        is_email = check_email(email_or_username)

        # Get the user from the database
        user = db.session.get(User, email_or_username) if is_email else Usernames.query.get(email_or_username)

        # Check if the user exists
        if user is None:
            if is_email: return {'message': f'No user found with the email    {email_or_username}', 'status': 'error'}, 401
            else:        return {'message': f'No user found with the username {email_or_username}', 'status': 'error'}, 401
        # Check if the user has solely signed up via Google
        if user.password is None: return {'message': 'You have signed up via Google, so please select "Continue with Google"', 'status': 'error'}, 401
        # Check if the password is correct
        if not checkpw(password.encode(), user.password.encode()): return {'message': 'Incorrect password', 'status': 'error'}, 401

        # Save the user's info in the session
        session['logged_in']            = True
        session['email']                = user.email
        session['username']             = user.username
        session['signed_up_via_google'] = False

        return {'url': session.pop('redirect_to', url_for(POST_LOGIN_REDIRECT)), 'status': 'redirect'}





class SignupAPI(Resource):
    def post(self):
        # Extract data
        data     = request.get_json()
        email    = data.get('email')
        username = data.get('username')
        password = data.get('password')
        if not email:              return {'message': 'Email not provided',    'status': 'error'}, 400
        if not username:           return {'message': 'Username not provided', 'status': 'error'}, 400
        if not password:           return {'message': 'Password not provided', 'status': 'error'}, 400
        if not check_email(email): return {'message': 'Invalid email',         'status': 'error'}, 400

        # Check if the email or username is already taken
        if User.query.get(email):            return {'message': 'Email already taken',    'status': 'error'}, 400
        if Usernames.query.get(username):    return {'message': 'Username already taken', 'status': 'error'}, 400

        # Hash the password
        password = hashpw(password.encode(), gensalt()).decode()
        # Add the user to the database
        user = User(email=email, username=username, password=password)
        db.session.add(user)
        db.session.add(Usernames(username=username, email=email))
        db.session.commit()
        # Save the user's info in the session
        session['logged_in'] = True
        session['email']     = email
        session['username']  = username

        return {'url': session.pop('redirect_to', url_for(POST_LOGIN_REDIRECT)), 'status': 'redirect'}





@auth_bp.route('/google-authorised/')
def page_google_authorised():
    # Get his info
    try: resp:Response = google.get('/oauth2/v1/userinfo')
    except TokenExpiredError: return redirect(url_for('auth.page_login'))
    except: return 'Internal Server Error', 500
    # Check if the responses are valid
    if not resp.ok:                    return f'Failed to fetch user info, please <a href="{url_for("auth.page_login")}">login again</a>', 500
    resp:dict = resp.json()
    if not resp.get('verified_email'): return 'Email not verified', 403
    if not resp.get('email'):          return 'Unable to fetch email', 500
    
    email = resp['email']
    user  = db.session.get(User, email)

    # If we have never seen this user before, add him to the database
    if not user:
        username = email.split('@')[0]
        user = User(email=resp['email'], username=resp['email'].split('@')[0])
        db.session.add(user)
        db.session.add(Usernames(username=username, email=email))
        db.session.commit()
    else:
        username = user.username
    # Save the user's info in the session
    session['logged_in']            = True
    session['email']                = email
    session['username']             = username
    session['signed_up_via_google'] = user.password is None

    return redirect( session.pop('redirect_to', url_for(POST_LOGIN_REDIRECT)) )





@auth_bp.route('/logout/')
@login_required()
def page_logout():
    session.clear()
    return redirect(url_for(POST_LOGOUT_REDIRECT))
    # return f'Successfully logged out. You may now return to the <a href="{url_for("root.page_index")}">homepage</a>'





class ChangeUsernameAPI(Resource):
    @login_required(json=True)
    def post(self):
        # Extract data
        new_username = request.get_json().get('new_username')
        if not new_username: return {'message': 'New username not provided', 'status': 'error'}, 400

        # Check if the username is a valid email address
        if check_email(new_username): return {'message': 'Username cannot be an email address', 'status': 'error'}, 400
        # Check if the username is already taken
        if Usernames.query.get(new_username): return {'message': 'Username already taken', 'status': 'error'}, 400
        # Check if the username is the same as the current one
        if session['username'] == new_username: return {'message': 'Please provide a username different from the current one', 'status': 'error'}, 400
        
        # Update the username
        user          = db.session.get(User, session['email'])
        old_username  = user.username
        user.username = new_username
        # Update the username in the Usernames table
        Usernames.query.get(old_username).username = new_username
        db.session.commit()
        
        # Update the session
        session['username'] = new_username
        
        return {'status': 'success'}





class ChangePasswordAPI(Resource):
    @login_required(json=True)
    def post(self):
        # Extract data
        data     = request.get_json()
        old_pass = data.get('current_password')
        new_pass = data.get('new_password')
        if not old_pass: return {'message': 'Old password not provided', 'status': 'error'}, 400
        if not new_pass: return {'message': 'New password not provided', 'status': 'error'}, 400
        
        user = db.session.get(User, session['email'])
        # Check if the user has signed up via Google
        if user.password is None: return {'message': 'You have signed up via Google, so you cannot change your password', 'status': 'error'}, 401
        # Check if the old password is correct
        if not checkpw(old_pass.encode(), user.password.encode()): return {'message': 'Incorrect password', 'status': 'error'}, 401
        # Check if the new password is the same as the old one
        if old_pass == new_pass: return {'message': 'Please provide a password different from the current one', 'status': 'error'}, 400
        
        # Update the password
        user.password = hashpw(new_pass.encode(), gensalt()).decode()
        db.session.commit()
        
        return {'status': 'success'}








