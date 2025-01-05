from flask import Blueprint, jsonify, render_template, request
from models import Reservation, Event, UserEvent, db
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
        # Fetch user-defined events
    user_events = UserEvent.query.filter_by(user_id=current_user.id).all()
    user_events_data = [{
        'id': f"user-{event.id}",
        'title': event.title,
        'start': event.start.isoformat(),
        'end': event.end.isoformat(),
        'description': event.description,
        'type': 'user_event'  # Add type for identification
    } for event in user_events]

    # Combine reservations and events
    combined_data = reservation_data + event_data + user_events_data

    return jsonify(combined_data)

@calendar_bp.route('/calendar', methods=['GET'])
@login_required
def view_calendar():
    return render_template('calendar.html')

@calendar_bp.route('/calendar/user-events', methods=['POST'])
@login_required
def create_user_event():
    data = request.json
    new_event = UserEvent(
        title=data['title'],
        start=data['start'],
        end=data['end'],
        description=data.get('description', ''),
        user_id=current_user.id
    )
    db.session.add(new_event)
    db.session.commit()
    return jsonify({'message': 'Event created successfully', 'event_id': new_event.id})

@calendar_bp.route('/calendar/user-events/<int:event_id>', methods=['DELETE'])
@login_required
def delete_user_event(event_id):
    event = UserEvent.query.get_or_404(event_id)
    if event.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    db.session.delete(event)
    db.session.commit()
    return jsonify({'message': 'Event deleted successfully'})