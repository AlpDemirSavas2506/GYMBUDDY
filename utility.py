from flask_mail import Message
from config import mail
from flask import render_template
from models import Notification, db

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

def send_reservation_email(user, f_start_time, f_end_time):
    """
    Send an email for slot reservation confirmation
    """
    html_body = render_template(
        'email/reservation_email.html',
        user_name=user.name,
        start_time=f_start_time,
        end_time=f_end_time
    )
    send_email('Reservation Confirmation', [user.email], html_body)

def send_cancellation_email(user, f_start_time, f_end_time):
    """
    Send an email for slot cancellation confirmation
    """
    html_body = render_template(
        'email/cancellation_email.html',
        user_name=user.name,
        start_time=f_start_time,
        end_time=f_end_time
    )
    send_email('Reservation Cancellation', [user.email], html_body)

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