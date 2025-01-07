# reservation_bp.py

from flask import Blueprint, render_template, request, jsonify
from models import User, Reservation, Facility, db
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from utility import send_reservation_email, send_cancellation_email, create_notification
from sqlalchemy.sql import func
from dateutil import parser
import pytz
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

reservation_bp = Blueprint('reservation_bp', __name__)

# Define local timezone
LOCAL_TIMEZONE = pytz.timezone('Europe/Istanbul')  # Adjust as needed

def truncate_datetime(dt):
    """Truncate datetime to remove seconds and microseconds."""
    return dt.replace(second=0, microsecond=0)

@reservation_bp.route('/reservation', methods=['GET', 'POST'])
@login_required
def reservation():
    if request.method == 'GET':
        facilities = Facility.query.filter_by(is_available=True).all()
        date = request.args.get('date')  # Optional date parameter
        facility_id = request.args.get('facility_id')  # Optional facility parameter

        if date and facility_id:
            try:
                # Parse date and facility
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                facility = Facility.query.get(facility_id)
                if not facility or not facility.is_available:
                    logger.debug(f"Facility unavailable: ID={facility_id}, Name={facility.name if facility else 'N/A'}")
                    return jsonify({'error': 'This facility is currently unavailable.'}), 403

                capacity = facility.capacity

                # Define opening and closing times in local timezone
                opening_time_local = datetime.combine(date_obj, datetime.strptime("08:00", "%H:%M").time())
                closing_time_local = datetime.combine(date_obj, datetime.strptime("22:00", "%H:%M").time())

                opening_time = LOCAL_TIMEZONE.localize(opening_time_local)
                closing_time = LOCAL_TIMEZONE.localize(closing_time_local)

                # Convert to UTC naive for filtering
                opening_time_utc = truncate_datetime(opening_time.astimezone(pytz.UTC)).replace(tzinfo=None)
                closing_time_utc = truncate_datetime(closing_time.astimezone(pytz.UTC)).replace(tzinfo=None)

                # Current time in local timezone
                now_local = datetime.now(LOCAL_TIMEZONE)

                # Define slot durations
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
                slot_duration = timedelta(minutes=60)  # Default 1-hour slot
                if facility.name in forty_minute_facilities:
                    slot_duration = timedelta(minutes=40)  # 40-minute slots

                # Fetch user's existing reservations within the UTC range
                user_reservations = Reservation.query.filter(
                    Reservation.facility_id == facility_id,
                    Reservation.user_id == current_user.id,
                    Reservation.start_time >= opening_time_utc,
                    Reservation.start_time < closing_time_utc
                ).all()

                # Convert user reservation times to UTC naive for matching
                user_reserved_slots = {
                    (res.start_time, res.end_time): res.id for res in user_reservations
                }
                logger.debug(f"User Reservations: {user_reserved_slots}")

                # Initialize slots
                slots = []
                current_time = opening_time

                while current_time < closing_time:
                    next_time = current_time + slot_duration

                    # If selected date is today and slot start time is before now, skip
                    if date_obj == now_local.date() and current_time < now_local:
                        logger.debug(f"Skipping past slot: {current_time}")
                        current_time = next_time
                        continue

                    # Convert slot times to UTC naive
                    current_time_utc = truncate_datetime(current_time.astimezone(pytz.UTC)).replace(tzinfo=None)
                    next_time_utc = truncate_datetime(next_time.astimezone(pytz.UTC)).replace(tzinfo=None)

                    logger.debug(f"Checking slot: {current_time_utc} to {next_time_utc}")

                    # Fetch reservations in the slot
                    reservations_in_slot = Reservation.query.filter(
                        Reservation.facility_id == facility_id,
                        Reservation.start_time == current_time_utc,
                        Reservation.end_time == next_time_utc
                    ).count()

                    logger.debug(f"Reservations in slot: {reservations_in_slot}")

                    available_capacity = capacity - reservations_in_slot

                    # Check if user has a reservation in this slot
                    reservation_id = user_reserved_slots.get((current_time_utc, next_time_utc), None)
                    is_reserved_by_user = reservation_id is not None

                    slot_info = {
                        'start_time': current_time.isoformat(),
                        'end_time': next_time.isoformat(),
                        'available': available_capacity > 0 or is_reserved_by_user,
                        'remaining_capacity': available_capacity if not is_reserved_by_user else available_capacity + 1,
                        'is_reserved_by_user': is_reserved_by_user,
                        'reservation_id': reservation_id if is_reserved_by_user else None
                    }

                    if not slot_info['available'] and not is_reserved_by_user:
                        # Optional: List users who have reserved this slot
                        slot_info['reserved_by'] = [res.user.username for res in Reservation.query.filter(
                            Reservation.facility_id == facility_id,
                            Reservation.start_time == current_time_utc,
                            Reservation.end_time == next_time_utc
                        ).all()]
                    slots.append(slot_info)

                    current_time = next_time

                logger.debug(f"Available slots: {slots}")

                return jsonify({'available_slots': slots})
            except Exception as e:
                logger.error(f"Error in GET /reservation: {e}")
                logger.error("Traceback:", exc_info=True)
                return jsonify({'error': 'An error occurred while fetching available slots.'}), 500

        return render_template('reservation.html', facilities=facilities)

    elif request.method == 'POST':
        data = request.get_json()
        operation = data.get('operation')  # 'create' or 'cancel'
        facility_id = data.get('facility_id')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        reservation_id = data.get('reservation_id')  # For cancellation

        if operation == 'cancel':
            if not reservation_id:
                logger.debug("Cancellation attempted without reservation_id.")
                return jsonify({'error': 'Reservation ID is required for cancellation.'}), 400

            # Fetch the reservation
            reservation = Reservation.query.filter_by(id=reservation_id, user_id=current_user.id).first()
            if not reservation:
                logger.debug(f"Cancellation attempted for non-existent or unauthorized reservation ID: {reservation_id}")
                return jsonify({'error': 'You can only cancel your own reservations.'}), 403

            # Check if the reservation is in the past
            current_time_utc = datetime.utcnow()
            logger.debug(f"Current UTC time: {current_time_utc}, Reservation end_time: {reservation.end_time}")
            if reservation.end_time < current_time_utc:
                logger.debug(f"Attempt to cancel past reservation ID: {reservation_id}")
                return jsonify({'error': 'Cannot cancel a past reservation.'}), 400

            try:
                # Delete the reservation
                db.session.delete(reservation)
                db.session.commit()
                logger.debug(f"Reservation ID {reservation_id} successfully canceled.")

                # Fetch the facility
                facility = Facility.query.get(reservation.facility_id)
                if not facility:
                    logger.error(f"Facility ID {reservation.facility_id} not found for reservation ID {reservation_id}.")
                    return jsonify({'error': 'Associated facility not found.'}), 500

                # Notification and email
                if 'reservation' in current_user.notification_preferences:
                    try:
                        create_notification(
                            user_id=current_user.id,
                            message=f"Your reservation for {facility.name} on {reservation.start_time.strftime('%Y-%m-%d %H:%M')} has been cancelled."
                        )

                        send_cancellation_email(
                            user=current_user,
                            f_facility_name=facility.name,
                            f_start_time=reservation.start_time,
                            f_end_time=reservation.end_time
                        )
                        logger.debug(f"Notification and cancellation email sent for reservation ID {reservation_id}.")
                    except Exception as notif_error:
                        logger.error(f"Error sending notification or email for cancellation: {notif_error}")
                        # Proceed without failing the cancellation

                return jsonify(success=True)
            except Exception as e:
                logger.error(f"Error canceling reservation ID {reservation_id}: {e}")
                logger.error("Traceback:", exc_info=True)
                return jsonify({'error': 'An error occurred while canceling the reservation.'}), 500

        elif operation == 'create':
            if not facility_id or not start_time or not end_time:
                logger.debug("Reservation creation attempted without all required details.")
                return jsonify({'error': 'Please provide all required details.'}), 400

            try:
                facility = Facility.query.get(facility_id)
                if not facility or not facility.is_available:
                    logger.debug(f"Reservation creation attempted for unavailable facility: ID={facility_id}, Name={facility.name if facility else 'N/A'}")
                    return jsonify({'error': 'This facility is currently unavailable.'}), 403

                # Parse start_time and end_time using dateutil for robustness
                start_time_dt = parser.isoparse(start_time)
                end_time_dt = parser.isoparse(end_time)

                # Handle timezone localization
                if start_time_dt.tzinfo is None:
                    # Naive datetime, localize it
                    start_time_dt = LOCAL_TIMEZONE.localize(start_time_dt)
                else:
                    # Aware datetime, convert to local timezone
                    start_time_dt = start_time_dt.astimezone(LOCAL_TIMEZONE)

                if end_time_dt.tzinfo is None:
                    # Naive datetime, localize it
                    end_time_dt = LOCAL_TIMEZONE.localize(end_time_dt)
                else:
                    # Aware datetime, convert to local timezone
                    end_time_dt = end_time_dt.astimezone(LOCAL_TIMEZONE)

                # Truncate datetime objects to remove seconds and microseconds
                start_time_dt = truncate_datetime(start_time_dt)
                end_time_dt = truncate_datetime(end_time_dt)

                # Convert to UTC and make naive for storage
                start_time_naive = truncate_datetime(start_time_dt.astimezone(pytz.UTC)).replace(tzinfo=None)
                end_time_naive = truncate_datetime(end_time_dt.astimezone(pytz.UTC)).replace(tzinfo=None)

                logger.debug(f"Creating reservation: Facility ID={facility_id}, Start={start_time_naive}, End={end_time_naive}")

                # Determine the local date of the reservation
                reservation_date = start_time_dt.date()

                # Define start and end of the day in local timezone
                start_of_day_local = LOCAL_TIMEZONE.localize(datetime.combine(reservation_date, datetime.min.time()))
                end_of_day_local = LOCAL_TIMEZONE.localize(datetime.combine(reservation_date, datetime.max.time()))

                # Convert to UTC naive
                start_of_day_utc = truncate_datetime(start_of_day_local.astimezone(pytz.UTC)).replace(tzinfo=None)
                end_of_day_utc = truncate_datetime(end_of_day_local.astimezone(pytz.UTC)).replace(tzinfo=None)

                # Capacity check
                existing_reservations_count = Reservation.query.filter(
                    Reservation.facility_id == facility_id,
                    Reservation.start_time == start_time_naive,
                    Reservation.end_time == end_time_naive
                ).count()

                logger.debug(f"Existing reservations count for slot: {existing_reservations_count}")

                if existing_reservations_count >= facility.capacity:
                    logger.debug(f"Capacity reached for slot: Start={start_time_naive}, End={end_time_naive}")
                    return jsonify({'error': 'The selected time slot has reached its capacity.'}), 400

                # Prevent the same user from reserving the same slot again
                user_existing_reservation = Reservation.query.filter(
                    Reservation.facility_id == facility_id,
                    Reservation.user_id == current_user.id,
                    Reservation.start_time == start_time_naive,
                    Reservation.end_time == end_time_naive
                ).first()

                if user_existing_reservation:
                    logger.debug(f"User {current_user.id} has already reserved slot: Start={start_time_naive}, End={end_time_naive}")
                    return jsonify({'error': 'You have already reserved this slot.'}), 400

                # Maximum daily reservations check
                existing_daily_reservations = Reservation.query.filter(
                    Reservation.user_id == current_user.id,
                    Reservation.facility_id == facility_id,
                    Reservation.start_time >= start_of_day_utc,
                    Reservation.start_time < end_of_day_utc
                ).count()

                logger.debug(f"Existing daily reservations for user: {existing_daily_reservations}")

                if existing_daily_reservations >= 2:
                    logger.debug(f"User {current_user.id} has reached daily reservation limit.")
                    return jsonify({'error': 'You can only reserve up to 2 slots for this facility on the same day.'}), 400

                # Create the new reservation
                new_reservation = Reservation(
                    user_id=current_user.id,
                    facility_id=facility_id,
                    start_time=start_time_naive,
                    end_time=end_time_naive
                )

                db.session.add(new_reservation)
                db.session.commit()

                logger.debug(f"Created reservation ID={new_reservation.id}")

                # Create notification and send email
                if 'reservation' in current_user.notification_preferences:
                    try:
                        create_notification(
                            user_id=current_user.id,
                            message=f"Your reservation for {facility.name} on {new_reservation.start_time.strftime('%Y-%m-%d %H:%M')} has been confirmed."
                        )

                        send_reservation_email(
                            user=current_user,
                            f_facility_name=facility.name,
                            f_start_time=new_reservation.start_time,
                            f_end_time=new_reservation.end_time
                        )
                        logger.debug(f"Notification and reservation email sent for reservation ID {new_reservation.id}.")
                    except Exception as notif_error:
                        logger.error(f"Error sending notification or email for reservation creation: {notif_error}")
                        # Proceed without failing the reservation

                return jsonify(success=True)
            except Exception as e:
                logger.error(f"Error creating reservation: {e}")
                logger.error("Traceback:", exc_info=True)
                return jsonify({'error': 'An error occurred while creating the reservation.'}), 500

    return jsonify(success=False)
