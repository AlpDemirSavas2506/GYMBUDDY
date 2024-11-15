from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp
from flask_wtf.file import FileField, FileAllowed


class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    email = StringField(
        'Email',
        validators=[DataRequired(), Email(message="Please enter a valid email address.")]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=6, message="Password must be at least 6 characters long.")
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password', message="Passwords must match.")
        ]
    )
    height = FloatField('Height', validators=[Optional()])
    weight = FloatField('Weight', validators=[Optional()])
    blood_type = StringField('Blood Type', validators=[Optional()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    emergency_contact_name = StringField('Emergency Contact Name', validators=[DataRequired()])
    emergency_contact_number = StringField('Emergency Contact Number', validators=[DataRequired()])
    submit = SubmitField('Sign Up')
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
