from flask_mail import Message
from config import mail
from flask import render_template

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