from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
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
