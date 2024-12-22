from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from models import User, Reservation, Facility, db
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from utility import send_reservation_email, send_cancellation_email, create_notification
from sqlalchemy.sql import func

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

            # Facility lists for different intervals
            one_hour_facilities = [
                "1 Nolu Açık Tenis Kortu (Merkez Tenis Kortları)",
                "1 Nolu Tenis Kortu (Büyük Spor Salonu)",
                "2 Nolu Açık Tenis Kortu (Merkez Tenis Kortları)",
                "2 Nolu Tenis Kortu (Büyük Spor Salonu)",
                "3 Nolu Açık Tenis Kortu (Merkez Tenis Kortları)",
                "3 Nolu Tenis Kortu (Büyük Spor Salonu)",
                "4 Nolu Kapalı Tenis Kortu (Merkez Tenis Kortları)",
                "5 Nolu Kapalı Tenis Kortu (Merkez Tenis Kortları)",
                "Açık Toprak Kort (Merkez Tenis Kortları)",
                "Baraka Spor Salonu - Ana Salon (Voleybol)",
                "Baraka Spor Salonu - Ana Salon (Basketbol)",
                "Halı Saha1",
                "Halı Saha2",
                "Halı Saha3",
                "1 Nolu Kapalı Tenis Kortu (Merkez Tenis Kortları)",
                "2 Nolu Kapalı Tenis Kortu (Merkez Tenis Kortları)",
            ]

            forty_minute_facilities = [
                "Baraka Spor Salonu - Fitness Salonu",
                "Baraka Spor Salonu - Minder Sporları Salonu",
                "Baraka Spor Salonu - Aynalı Salon",
                "Baraka Spor Salonu Stadyum",
                "ODTÜKENT Spor Merkezi- Squash Kortu 1",
                "ODTÜKENT Spor Merkezi- Squash Kortu 2",
            ]

            # Determine slot duration based on facility
            slot_duration = timedelta(minutes=60)  # Default to 1-hour slots
            facility = Facility.query.get(facility_id)
            if facility.name in forty_minute_facilities:
                slot_duration = timedelta(minutes=40)  # 40-minute slots for specific facilities

            # Fetch existing reservations with eager loading
            existing_reservations = Reservation.query.filter(
                Reservation.facility_id == facility_id,
                Reservation.start_time >= opening_time,
                Reservation.end_time <= closing_time
            ).join(User, Reservation.user_id == User.id).all()

            # Create a list of reserved slots with their usernames
            reserved_slots = []
            for res in existing_reservations:
                reserved_slots.append({
                    'id': res.id,
                    'start_time': res.start_time.isoformat(),
                    'end_time': res.end_time.isoformat(),
                    'username': res.user.username
                })

            # Build available slots
            slots = []
            current_time = opening_time
            while current_time < closing_time:
                next_time = current_time + slot_duration
                overlapping_reservation = next(
                    (res for res in reserved_slots
                     if res['start_time'] < next_time.isoformat() and res['end_time'] > current_time.isoformat()),
                    None
                )

                if overlapping_reservation:
                    slots.append({
                        'reservation_id': overlapping_reservation['id'],
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
        operation = data.get('operation')  # Check if it's a cancel operation
        facility_id = data.get('facility_id')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        reservation_id = data.get('reservation_id')  # For cancellation

        if operation == 'cancel':
            reservation = Reservation.query.filter_by(id=reservation_id, user_id=current_user.id).first()
            facility = Facility.query.get(reservation.facility_id)
            if not reservation:
                return jsonify({'error': 'You can only cancel your own reservations.'}), 403

            try:
                db.session.delete(reservation)
                db.session.commit()

                # Create a notification for the user
                create_notification(
                user_id=current_user.id,
                message=f"Your reservation for {facility.name} on start date: {reservation.start_time} end date: {reservation.end_time} has been cancelled."
                )
                
                send_cancellation_email(
                    user=current_user,
                    f_facility_name=facility.name,
                    f_start_time=reservation.start_time,
                    f_end_time=reservation.end_time
                )

                return jsonify(success=True)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        elif operation == 'create':
            if not facility_id or not start_time or not end_time:
                return jsonify({'error': 'Please provide all required details.'}), 400

            try:
                start_time = datetime.fromisoformat(start_time)
                end_time = datetime.fromisoformat(end_time)

                conflicting_reservation = Reservation.query.filter(
                    Reservation.facility_id == facility_id,
                    Reservation.start_time < end_time,
                    Reservation.end_time > start_time
                ).first()

                if conflicting_reservation:
                    return jsonify({'error': 'The selected time slot is already booked.'}), 400
                
                # Check how many reservations exist for the same facility and day
                existing_reservations_count = Reservation.query.filter(
                    Reservation.user_id == current_user.id,
                    Reservation.facility_id == facility_id,
                    func.date(Reservation.start_time) == func.date(start_time)  # Compare only the date
                ).count()

                if existing_reservations_count >= 2:
                    return jsonify({'error': 'You can only reserve up to 2 slots for this facility on the same day.'}), 400

                new_reservation = Reservation(
                    user_id=current_user.id,
                    facility_id=facility_id,
                    start_time=start_time,
                    end_time=end_time
                )
                facility = Facility.query.get(new_reservation.facility_id)

                db.session.add(new_reservation)
                db.session.commit()
                
                # Create a notification for the user
                create_notification(
                    user_id=current_user.id,
                    message=f"Your reservation for {facility.name} on start date: {new_reservation.start_time} end date: {new_reservation.end_time} has been confirmed."
                )

                send_reservation_email(
                    user=current_user,
                    f_facility_name=facility.name,
                    f_start_time=new_reservation.start_time,
                    f_end_time=new_reservation.end_time
                )

                return jsonify(success=True)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        return jsonify(success=False)
