from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from models import db, User
from auth.routes import auth_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'JUf6cQGC'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:alp.demir@localhost/GymBuddy'
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth_bp.login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app.register_blueprint(auth_bp)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
