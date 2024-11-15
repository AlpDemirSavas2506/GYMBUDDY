from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash
from .forms import SignupForm, LoginForm
from models import User, db

auth_bp = Blueprint('auth_bp', __name__)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already exists. Please log in.')
            return redirect(url_for('auth_bp.login'))

        new_user = User(
            username=form.username.data,
            name=form.name.data,
            surname=form.surname.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            emergency_contact_name=form.emergency_contact_name.data,
            emergency_contact_number=form.emergency_contact_number.data,
            height=form.height.data,
            weight=form.weight.data,
            blood_type=form.blood_type.data
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.')
        return redirect(url_for('auth_bp.login'))
    return render_template('signup.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('home'))  # Redirect to home page
        else:
            flash('Invalid username or password.')
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('auth_bp.login'))
@auth_bp.route('/send_verification_code', methods=['POST'])
@login_required
def send_verification_code():
    verification_code = str(random.randint(100000, 999999))
    session['verification_code'] = verification_code

    msg = Message("Your Password Change Verification Code",
                  sender=current_app.config['MAIL_USERNAME'],  # Use app context
                  recipients=[current_user.email])
    msg.body = f"Your verification code is: {verification_code}"

    with current_app.app_context():
        mail = current_app.extensions['mail']  # Access mail from app context
        mail.send(msg)

    flash("Verification code sent to your email.")
    return redirect(url_for('auth_bp.profile'))

@auth_bp.route('/verify_code', methods=['POST'])
@login_required
def verify_code():
    user_code = request.form['verification_code']
    if session.get('verification_code') == user_code:
        session['password_change_allowed'] = True
        flash("Verification successful. You can now change your password.")
    else:
        flash("Invalid verification code.")
    return redirect(url_for('auth_bp.profile'))

@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    if not session.get('password_change_allowed'):
        flash("Please verify your email before changing the password.")
        return redirect(url_for('auth_bp.profile'))

    new_password = request.form['new_password']
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    session.pop('password_change_allowed', None)
    flash("Password changed successfully.")
    return redirect(url_for('auth_bp.profile'))