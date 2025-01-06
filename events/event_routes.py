from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import current_user

from models import Event, db, User
import io
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, FileField, SubmitField
from wtforms.validators import DataRequired

events_bp = Blueprint('events_bp', __name__)

# Form for creating events
class EventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    event_date = DateField('Event Date', validators=[DataRequired()])
    image = FileField('Image (Optional)')
    submit = SubmitField('Create Event')

from utility import create_notification, send_event_created_email

@events_bp.route('/events', methods=['GET', 'POST'])
def events():
    form = EventForm()
    if form.validate_on_submit():
        image_data = form.image.data.read() if form.image.data else None
        new_event = Event(
            title=form.title.data,
            description=form.description.data,
            event_date=form.event_date.data,
            image=image_data
        )
        db.session.add(new_event)
        db.session.commit()

        # Notify users who want event notifications
        users = User.query.filter(User.notification_preferences.contains(['events'])).all()
        for user in users:
            create_notification(
                user_id=user.id,
                message=f"New event created: {new_event.title} on {new_event.event_date.strftime('%Y-%m-%d')}"
            )

            send_event_created_email(
                user=user,
                f_event_title=new_event.title,
                f_event_date=new_event.event_date.strftime('%Y-%m-%d'),
                f_event_image=new_event.image
            )

        flash('Event created successfully!', 'success')
        return redirect(url_for('events_bp.events'))

    events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template('events.html', form=form, events=events)

@events_bp.route('/events/image/<int:event_id>')
def event_image(event_id):
    event = Event.query.get_or_404(event_id)
    if event.image:
        return send_file(
            io.BytesIO(event.image),
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f'event_{event_id}.jpg'
        )
    else:
        flash('No image found for this event.', 'warning')
        return redirect(url_for('events_bp.events'))
@events_bp.route('/delete-event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if not current_user.is_admin():  # Only admins can delete events
        flash("You do not have permission to delete events.", "danger")
        return redirect(url_for('events_bp.events'))

    event = Event.query.get(event_id)
    if not event:
        flash("Event not found.", "danger")
        return redirect(url_for('events_bp.events'))

    db.session.delete(event)
    db.session.commit()
    flash("Event deleted successfully.", "success")
    return redirect(url_for('events_bp.events'))