from flask_mail import Message
from config import mail
from flask import render_template
from models import Notification, db
import base64

def send_email(subject, recipient, html_body):
    msg = Message(
        subject=subject,
        sender="trtstajtest@gmail.com",  # Replace with your app's email
        recipients=recipient
    )
    msg.html = html_body
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_reservation_email(user, f_facility_name, f_start_time, f_end_time):
    """
    Send an email for slot reservation confirmation
    """
    html_body = render_template(
        'email/reservation_email.html',
        user_name=user.name,
        facility_name=f_facility_name,
        start_time=f_start_time,
        end_time=f_end_time
    )
    send_email('Reservation Confirmation', [user.email], html_body)

def send_cancellation_email(user, f_facility_name, f_start_time, f_end_time):
    """
    Send an email for slot cancellation confirmation
    """
    html_body = render_template(
        'email/cancellation_email.html',
        user_name=user.name,
        facility_name=f_facility_name,
        start_time=f_start_time,
        end_time=f_end_time
    )
    send_email('Reservation Cancellation', [user.email], html_body)

def get_image_base64(binary_data):
    """
    Convert binary image data to a base64-encoded string.
    """
    return f"data:image/png;base64,{base64.b64encode(binary_data).decode('utf-8')}"

def send_event_created_email(user, f_event_title, f_event_date, f_event_image):
    """
    Send an email for newly created events
    """
    event_image_base64 = get_image_base64(f_event_image) if f_event_image else None

    html_body = render_template(
        'event/event_created_email.html',
        user_name=user.name,
        event_title=f_event_title,
        event_date=f_event_date,
        event_image=event_image_base64
    )
    send_email(f'New event: {f_event_title}', [user.email], html_body)

def send_topic_created_email(user, f_topic_title, f_topic_creator_name, f_message):
    """
    Send an email for newly created forum topics
    """
    html_body = render_template(
        'forum/forum_topic_created_email.html',
        user_name=user.name,
        topic_title=f_topic_title,
        topic_creator_name=f_topic_creator_name,
        message=f_message
    )
    send_email(f'New forum topic: {f_topic_title} created by {f_topic_creator_name}', [user.email], html_body)

def create_notification(user_id, message):
    """
    Create a new notification for a user.
    """
    notification = Notification(user_id=user_id, message=message)
    db.session.add(notification)
    db.session.commit()

def get_notifications(user_id):
    """
    Fetch all notifications for a user.
    """
    return Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()

def mark_notification_as_read(notification_id):
    """
    Mark a notification as read.
    """
    notification = Notification.query.get(notification_id)
    if notification:
        notification.is_read = True
        db.session.commit()