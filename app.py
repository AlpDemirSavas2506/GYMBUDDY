import os
from flask_login import LoginManager, login_required, current_user
from reservation.routes import reservation_bp
from models import db, User, Notification, Reservation
from auth.forms import UpdateProfileForm
from config import mail
from dotenv import load_dotenv
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, redirect, url_for, flash, request


def create_app():
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)

    # Use environment variables for configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

    # Email configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

    # Initialize extensions
    mail.init_app(app)
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth_bp.login'
    login_manager.init_app(app)

    # Define routes and views...
    @app.route('/home')
    @login_required
    def home():
        today = datetime.now()
        upcoming_reservations = [
            reservation for reservation in current_user.reservations if reservation.start_time >= today
        ]
        past_reservations = [
            reservation for reservation in current_user.reservations if reservation.start_time < today
        ]
        return render_template(
            'home.html',
            upcoming_reservations=upcoming_reservations,
            past_reservations=past_reservations,
        )
    @app.context_processor
    def inject_datetime():
        return {'datetime': datetime, 'timedelta': timedelta}
    @app.route('/profile')
    @login_required
    def profile():
        form = UpdateProfileForm(obj=current_user)
        return render_template('profile.html', user=current_user, form=form)

    @app.route('/notifications/mark-read', methods=['POST'])
    @login_required
    def mark_notifications_as_read():
        # Query for unread notifications for the current user
        unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()

        # Mark all unread notifications as read
        for notification in unread_notifications:
            notification.is_read = True

        db.session.commit()  # Commit the changes to the database

        return jsonify({"success": True, "unread_count": 0})  # Respond with updated count
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from auth.routes import auth_bp
    from forum.forum_routes import forum_bp
    from events.event_routes import events_bp
    from notification.notification_routes import notification_bp
    from local_calendar.calendar_routes import calendar_bp
    from admin.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(reservation_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(404)
    def page_not_found(e):
        if current_user.is_authenticated:
            return render_template('404.html'), 404
        else:
            flash("Page not found. Please log in again.", "warning")
            return redirect(url_for('auth_bp.login'))

    @app.route('/')
    def index():
        return redirect(url_for('auth_bp.login'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host = '0.0.0.0', port = 5000, debug=True)
