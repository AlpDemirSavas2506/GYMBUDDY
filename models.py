from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import BYTEA

db = SQLAlchemy()
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    name = db.Column(db.String(150), nullable=False)
    surname = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(150), nullable=False)
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    blood_type = db.Column(db.String(10))
    phone_number = db.Column(db.String(20))
    emergency_contact_name = db.Column(db.String(150))
    emergency_contact_number = db.Column(db.String(20))
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)