from flask import Blueprint, jsonify, render_template
from models import Reservation, Event
from datetime import datetime
from flask_login import current_user, login_required

calendar_bp = Blueprint('calendar_bp', __name__)

@calendar_bp.route('/api/calendar', methods=['GET'])
@login_required
def get_calendar_data():
    # Fetch reservations
    reservations = Reservation.query.filter_by(user_id=current_user.id).all()
    reservation_data = [
        {
            "id": f"reservation-{res.id}",
            "title": f"Reservation: {res.facility.name}",
            "start": res.start_time.isoformat(),
            "end": res.end_time.isoformat(),
            "description": "",  # No description for reservations
            "type": "reservation"
        }
        for res in reservations
    ]

    # Fetch university events (use event_date for both start and end)
    events = Event.query.all()
    event_data = [
        {
            "id": f"event-{event.id}",
            "title": f"Event: {event.title}",
            "start": event.event_date.isoformat(),  # Use event_date for start
            "end": event.event_date.isoformat(),    # Use event_date for end
            "description": event.description,
            "type": "event"
        }
        for event in events
    ]

    # Combine reservations and events
    combined_data = reservation_data + event_data

    return jsonify(combined_data)

@calendar_bp.route('/calendar', methods=['GET'])
@login_required
def view_calendar():
    return render_template('calendar.html')

