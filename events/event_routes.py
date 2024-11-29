from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from models import Event, db
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
