from flask_mail import Message
from config import mail

def send_email(subject, recipient, body):
    msg = Message(
        subject=subject,
        sender="trtstajtest@gmail.com",  # Replace with your app's email
        recipients=[recipient]
    )
    msg.body = body
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")