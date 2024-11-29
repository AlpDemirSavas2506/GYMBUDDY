from random import randint  # Replace this

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import mail
from .forms import SignupForm, LoginForm, UpdateProfileForm
from models import User, Reservation, Facility
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db

auth_bp = Blueprint('auth_bp', __name__)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    error_message = None
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            error_message = "Passwords do not match."
        elif User.query.filter_by(email=form.email.data).first():
            error_message = "Email already exists."
        elif User.query.filter_by(username=form.username.data).first():
            error_message = "Username already exists."
        else:
            # Create and save user
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
                blood_type=form.blood_type.data,
            )
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! Please log in.')
            return redirect(url_for('auth_bp.login'))
    return render_template('signup.html', form=form, error_message=error_message)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error_message = None  # Initialize error_message to avoid UnboundLocalError
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            error_message = 'Logged in successfully.'
            return redirect(url_for('home'))
        else:
            error_message = "Invalid username or password."
    return render_template('login.html', form=form, error_message=error_message)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('auth_bp.login'))


from flask_mail import Message
from flask import request, session, current_app


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.name = form.name.data
        current_user.surname = form.surname.data
        current_user.email = form.email.data
        current_user.phone_number = form.phone_number.data
        current_user.emergency_contact_name = form.emergency_contact_name.data
        current_user.emergency_contact_number = form.emergency_contact_number.data
        current_user.height = form.height.data
        current_user.weight = form.weight.data
        current_user.blood_type = form.blood_type.data
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('auth_bp.profile'))

    if request.method == 'POST':
        if request.form.get('action') == 'send_verification_code':
            verification_code = str(randint(100000, 999999))
            session['verification_code'] = verification_code

            msg = Message(
                "Your Email Verification Code",
                sender=current_app.config['MAIL_USERNAME'],
                recipients=[current_user.email]
            )
            msg.body = f"Your verification code is: {verification_code}"
            with current_app.app_context():
                mail.send(msg)
            flash("Verification code sent to your email.", "info")

        elif request.form.get('action') == 'verify_code':
            entered_code = request.form.get('verification_code')
            if entered_code == session.get('verification_code'):
                flash("Verification successful!", "success")
                session.pop('verification_code', None)  # Remove the code after verification
            else:
                flash("Invalid verification code. Please try again.", "danger")

    return render_template('profile.html', user=current_user, form=form)


from flask import jsonify


@auth_bp.route('/send-verification-code', methods=['POST'])
@login_required
def send_verification_code():
    verification_code = str(randint(100000, 999999))
    session['verification_code'] = verification_code

    msg = Message(
        "Your Email Verification Code",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[current_user.email]
    )
    msg.body = f"Your verification code is: {verification_code}"

    try:
        with current_app.app_context():
            mail.send(msg)
        return jsonify(success=True)
    except Exception as e:
        print(e)
        return jsonify(success=False)


@auth_bp.route('/verify-code', methods=['POST'])
@login_required
def verify_code():
    data = request.get_json()
    entered_code = data.get('code')
    if entered_code == session.get('verification_code'):
        session.pop('verification_code', None)
        return jsonify(success=True)
    return jsonify(success=False)


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    new_password = data.get('password')

    if not new_password:
        return jsonify(success=False)

    current_user.set_password(new_password)
    db.session.commit()
    return jsonify(success=True)


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        verification_code = request.form.get('verification_code')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if verification_code != session.get('verification_code'):
            flash("Invalid verification code.", "danger")
            return redirect(url_for('auth_bp.reset_password'))

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('auth_bp.reset_password'))

        email = session.get('reset_email')
        user = User.query.filter_by(email=email).first()

        if user:
            user.set_password(new_password)
            db.session.commit()
            session.pop('reset_email', None)
            session.pop('verification_code', None)
            flash("Password reset successful. You can now log in.", "success")
            return redirect(url_for('auth_bp.login'))

        flash("Something went wrong. Please try again.", "danger")

    return render_template('reset_password.html')


from flask_mail import Message
from random import randint


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate a verification code
            verification_code = str(randint(100000, 999999))
            session['reset_email'] = email
            session['verification_code'] = verification_code

            # Send email with verification code
            msg = Message(
                "Password Reset Verification Code",
                sender=current_app.config['MAIL_USERNAME'],
                recipients=[email]
            )
            msg.body = f"Your password reset verification code is: {verification_code}"
            mail.send(msg)

            flash("A verification code has been sent to your email.", "info")
            return redirect(url_for('auth_bp.reset_password'))

        flash("Email not found. Please check and try again.", "danger")

    return render_template('forgot_password.html')

