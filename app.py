from flask import Flask
from flask_login import LoginManager
from reservation.routes import reservation_bp
from models import db, User
from flask_login import login_required
from auth.forms import UpdateProfileForm
from config import mail
from datetime import datetime



def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'JUf6cQGC'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:alp.demir@localhost/GymBuddy'

    # Email configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'trtstajtest@gmail.com'
    app.config['MAIL_PASSWORD'] = 'kzbx faau iopp ofjw'

    mail.init_app(app)
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth_bp.login'
    login_manager.init_app(app)

    @app.route('/home')
    @login_required
    def home():
        today = datetime.now()

        # Rezervasyonları tarihine göre ayır
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
    @app.route('/events')
    @login_required
    def events():
        return render_template('events.html')

    @app.route('/forum')
    @login_required
    def forum():
        return render_template('forum.html')


    @app.route('/profile')
    @login_required
    def profile():
        form = UpdateProfileForm(obj=current_user)
        return render_template('profile.html', user=current_user, form=form)
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from auth.routes import auth_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(reservation_bp)

    @app.errorhandler(404)
    def page_not_found(e):
        # Check if the user is authenticated
        if current_user.is_authenticated:
            logout_user()
            return redirect(url_for('auth_bp.login'))
        else:
            # For non-authenticated users, redirect to login with a message
            return redirect(url_for('auth_bp.login'))

    # Define routes
    @app.route('/')
    def index():
        return redirect(url_for('auth_bp.login'))

    return app
from flask import render_template, redirect, url_for
from flask_login import logout_user, current_user


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
