from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from models import Notification, db
from utility import get_notifications, mark_notification_as_read

notification_bp = Blueprint('notifications', __name__)

@notification_bp.route('/notifications', methods=['GET'])
@login_required
def fetch_notifications():
    """
    Fetch all notifications for the logged-in user.
    """
    notifications = get_notifications(current_user.id)
    return jsonify([n.to_dict() for n in notifications])

@notification_bp.route('/notifications/<int:notification_id>', methods=['POST'])
@login_required
def read_notification(notification_id):
    """
    Mark a notification as read.
    """
    mark_notification_as_read(notification_id)
    return jsonify({"message": "Notification marked as read."})

@notification_bp.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
    if notification:
        db.session.delete(notification)
        db.session.commit()
        return jsonify({"success": True, "message": "Notification deleted."})
    return jsonify({"success": False, "message": "Notification not found."}), 404

@notification_bp.route('/notifications/clear', methods=['POST'])
@login_required
def clear_notifications():
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"success": True, "message": "All notifications cleared."})
