from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp, NumberRange


class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(message="Please enter a valid email address."),
            Regexp(r".+@metu\.edu\.tr$", message="Email must be a valid METU address (e.g., example@metu.edu.tr).")
        ]
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
    height = FloatField(
        'Height (cm)',
        validators=[
            Optional(),
            NumberRange(min=50.0, max=250.0, message="Height must be between 50.00 and 250.00 cm.")
        ]
    )
    weight = FloatField(
        'Weight (kg)',
        validators=[
            Optional(),
            NumberRange(min=20.0, max=300.0, message="Weight must be between 20.00 and 300.00 kg.")
        ]
    )
    blood_type = StringField('Blood Type', validators=[Optional()])
    phone_number = StringField(
        'Phone Number',
        validators=[
            DataRequired(),
            Regexp(r'^\d+$', message="Phone number must contain only digits.")
        ]
    )
    emergency_contact_name = StringField('Emergency Contact Name', validators=[DataRequired()])
    emergency_contact_number = StringField('Emergency Contact Number', validators=[DataRequired()])
    submit = SubmitField('Sign Up')
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(message="Please enter a valid email address."),
            Regexp(r".+@metu\.edu\.tr$", message="Email must be a valid METU address (e.g., example@metu.edu.tr).")
        ]
    )
    phone_number = StringField(
        'Phone Number',
        validators=[
            DataRequired(),
            Regexp(r'^\d+$', message="Phone number must contain only digits.")
        ]
    )
    emergency_contact_name = StringField('Emergency Contact Name', validators=[DataRequired()])
    emergency_contact_number = StringField('Emergency Contact Number', validators=[DataRequired()])
    height = FloatField(
        'Height',
        validators=[
            Optional(),
            NumberRange(min=50.0, max=250.0, message="Height must be between 50.00 and 250.00 cm.")
        ]
    )
    weight = FloatField(
        'Weight',
        validators=[
            Optional(),
            NumberRange(min=20.0, max=300.0, message="Weight must be between 20.00 and 300.00 kg.")
        ]
    )
    blood_type = StringField('Blood Type', validators=[Optional()])
    submit = SubmitField('Update Profile')

class CreateTopicForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=255)])
    explanation = StringField('Explanation', validators=[DataRequired()])
    submit = SubmitField('Create Topic')

class ReplyForm(FlaskForm):
    content = StringField('Reply', validators=[DataRequired()])
    submit = SubmitField('Post Reply')

from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, SubmitField
from wtforms.validators import DataRequired

class NotificationPreferencesForm(FlaskForm):
    preferences = SelectMultipleField(
        'Select Notifications You Want to Receive:',
        choices=[
            ('reservation', 'Reservation Notifications'),
            ('forum', 'Forum Notifications'),
            ('events', 'Event Notifications')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Save Preferences')

