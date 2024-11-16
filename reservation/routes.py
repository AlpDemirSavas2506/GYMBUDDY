from flask import Blueprint, render_template, redirect, url_for, flash
from models import User, Reservation, Facility
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db

reservation_bp = Blueprint('reservation_bp', __name__)


@reservation_bp.route('/reservation', methods=['GET', 'POST'])
@login_required
def reservation():
    if request.method == 'GET':
        facilities = Facility.query.all()
        date = request.args.get('date')  # Optional query parameter for date
        facility_id = request.args.get('facility_id')  # Optional facility parameter

        if date and facility_id:
            # Parse date and set facility
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            opening_time = datetime.combine(date_obj, datetime.strptime("08:00", "%H:%M").time())
            closing_time = datetime.combine(date_obj, datetime.strptime("22:00", "%H:%M").time())
            slot_duration = timedelta(minutes=30)

            # Fetch existing reservations
            existing_reservations = Reservation.query.filter(
                Reservation.facility_id == facility_id,
                Reservation.start_time >= opening_time,
                Reservation.end_time <= closing_time
            ).join(User, Reservation.user_id == User.id).all()

            # Create a list of reserved slots with their usernames
            reserved_slots = []
            for res in existing_reservations:
                reserved_slots.append({
                    'start_time': res.start_time,
                    'end_time': res.end_time,
                    'username': res.user.username
                })

            # Build available slots
            slots = []
            current_time = opening_time
            while current_time < closing_time:
                next_time = current_time + slot_duration
                # Check if this time overlaps with any reserved slot
                overlapping_reservation = next(
                    (res for res in reserved_slots
                     if res['start_time'] < next_time and res['end_time'] > current_time),
                    None
                )

                if overlapping_reservation:
                    slots.append({
                        'start_time': current_time.isoformat(),
                        'end_time': next_time.isoformat(),
                        'available': False,
                        'username': overlapping_reservation['username']
                    })
                else:
                    slots.append({
                        'start_time': current_time.isoformat(),
                        'end_time': next_time.isoformat(),
                        'available': True
                    })

                current_time = next_time

            return jsonify({'available_slots': slots})

        return render_template('reservation.html', facilities=facilities)

    elif request.method == 'POST':
        data = request.get_json()
        facility_id = data.get('facility_id')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if not facility_id or not start_time or not end_time:
            flash('Please fill in all fields', 'danger')
            return jsonify(success=False)

        try:
            start_time = datetime.fromisoformat(start_time)
            end_time = datetime.fromisoformat(end_time)

            # Check for conflicts
            conflicting_reservation = Reservation.query.filter(
                Reservation.facility_id == facility_id,
                Reservation.start_time < end_time,
                Reservation.end_time > start_time
            ).first()

            if conflicting_reservation:
                flash('The selected time slot is already booked', 'danger')
                return jsonify(success=False)

            # Save reservation
            new_reservation = Reservation(
                user_id=current_user.id,
                facility_id=facility_id,
                start_time=start_time,
                end_time=end_time
            )
            db.session.add(new_reservation)
            db.session.commit()
            return jsonify(success=True)

        except Exception as e:
            return jsonify({'error': str(e)}), 500