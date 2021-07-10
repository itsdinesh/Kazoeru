import json
import time

from flask import Blueprint, render_template, url_for, redirect, request, flash, make_response, Response, jsonify
from flask_login import login_user, login_required, logout_user, current_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# init SQLAlchemy so we can use it later in our models
from people_counter import Camera

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    name = db.Column(db.String)
    role = db.Column(db.String, default="user")


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'kazoeru-is-the-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from app import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    return app


def requires_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if current_user.role not in roles and current_user.role == 'user':
                # Redirect the user to an unauthorized notice to user dashboard!
                flash('User is not authorised to access staff services.')
                return redirect(url_for('auth.user_dashboard'))

            if current_user.role not in roles and current_user.role == 'operator':
                # Redirect the user to an unauthorized notice to staff dashboard!
                flash('Staff is not authorised to access regular user services.')
                return redirect(url_for('auth.staff_dashboard'))

            return f(*args, **kwargs)

        return wrapped

    return wrapper


auth = Blueprint('auth', __name__)


@auth.route('/')
def index():
    return render_template('index.html')


@auth.route('/about')
def about():
    return render_template('about.html')


@auth.route('/login')
def login():
    if current_user.is_authenticated and current_user.role == 'operator':
        return redirect(url_for('auth.staff_dashboard'))
    elif current_user.is_authenticated and current_user.role == 'user':
        return redirect(url_for('auth.user_dashboard'))
    else:
        return render_template('login.html')


@auth.route('/profile')
@login_required
@requires_roles('user')
def profile():
    return render_template('profile.html', name=current_user.name)


@auth.route('/user-dashboard')
@login_required
@requires_roles('user')
def user_dashboard():
    gen(Camera())  # Start running OpenCV video.
    return render_template('userdashboard.html', name=current_user.name)


@auth.route('/staff-dashboard')
@login_required
@requires_roles('operator')
def staff_dashboard():
    return render_template('staffdashboard.html', name=current_user.name)


@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if user is None:
        flash('An user account does not exist in this email.')
        return redirect(
            url_for('auth.login'))  # if the user doesn't exist or password is wrong, reload the page

    elif user.role == "operator":
        flash('Please use the staff login to log into your account.')
        return redirect(url_for('auth.login'))

    elif not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))  # if the user doesn't exist or password is wrong, reload the page

    # if the check pass, then we know the user has the right credentials
    elif user.role == "user":
        login_user(user, remember=remember)
        return redirect(url_for('auth.user_dashboard'))


@auth.route('/staff-login')
def operatorlogin():
    if current_user.is_authenticated and current_user.role == 'operator':
        return redirect(url_for('auth.staff_dashboard'))
    elif current_user.is_authenticated and current_user.role == 'user':
        return redirect(url_for('auth.user_dashboard'))
    else:
        return render_template('stafflogin.html')


@auth.route('/staff-login', methods=['POST'])
def operatorlogin_post(*roles):
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database

    if user is None:
        flash('An user account does not exist in this email.')
        return redirect(
            url_for('auth.operatorlogin'))  # if the user doesn't exist or password is wrong, reload the page

    elif user.role == "user":
        flash('Please use the regular user login to log into your account.')
        return redirect(url_for('auth.operatorlogin'))

    elif user.email == email and check_password_hash(user.password, password) and user.role == 'operator':
        # if the above check passes, then we know the user has the right credentials
        login_user(user, remember=remember)
        return redirect(url_for('auth.staff_dashboard'))

    elif not user or not check_password_hash(user.password, password) or user is None:
        flash('Please check your login details and try again.')
        return redirect(
            url_for('auth.operatorlogin'))  # if the user doesn't exist or password is wrong, reload the page




@auth.route('/register')
def register():
    return render_template('register.html')


@auth.route('/register', methods=['POST'])
def register_post():
    # code to validate and add user to database goes here
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    user = User.query.filter_by(
        email=email).first()  # if this returns a user, then the email already exists in database

    if user:  # if a user is found, we want to redirect back to register page so user can try again
        flash('Email address already exists!')
        return redirect(url_for('auth.register'))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    flash('Registration successful, please log into your account in the fields below!')
    return redirect(url_for('auth.login'))


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.index'))


@auth.route('/data')
def data():
    status = Camera.get_crowd_count()
    data = [(time.time() + 28800) * 1000, status[0]]
    response = make_response(json.dumps(data))
    response.content_type = 'application/json'
    return response


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@auth.route('/video-feed', methods=['GET'])
@login_required
@requires_roles('operator')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@auth.route('/crowd-data', methods=['GET'])
def crowd_data():
    status = Camera.get_crowd_count()

    return jsonify(
        crowd_count=status[0],
        crowd_status=status[1],
        train_status=status[2]
    )


@auth.route('/oldindex')
def test_feed():
    return render_template('OLD/video.html')


application = create_app()

if __name__ == '__main__':
    application.run(host='0.0.0.0')
