from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from models import db, User
from flask import render_template
from flask_login import login_required, current_user
mail = Mail()  # Initialize mail globally


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
        return render_template('home.html')

    @app.route('/events')
    @login_required
    def events():
        return render_template('events.html')

    @app.route('/reservation')
    @login_required
    def reservation():
        return render_template('reservation.html')

    @app.route('/forum')
    @login_required
    def forum():
        return render_template('forum.html')

    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html', user=current_user)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    # Define routes
    @app.route('/')
    def index():
        return redirect(url_for('auth_bp.login'))

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
