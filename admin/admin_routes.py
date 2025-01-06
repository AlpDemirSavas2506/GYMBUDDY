from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Facility, Reservation, db
from utility import admin_required

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

# Admin dashboard
@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    if not current_user.is_admin():
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for('main_bp.home'))  # Redirect to a safe page

    return render_template('admin/dashboard.html')

# Manage facility availability
@admin_bp.route('/facilities', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_facilities():
    if not current_user.is_admin():
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for('main_bp.home'))

    facilities = Facility.query.all()

    if request.method == 'POST':
        # Get facility ID from form
        facility_id = request.form.get('facility_id')
        # Toggle availability
        facility = Facility.query.get(facility_id)
        if facility:
            facility.is_available = not facility.is_available  # Toggle the value
            db.session.commit()
            status = "available" if facility.is_available else "unavailable"
            flash(f"Facility '{facility.name}' is now {status}.", "success")
        else:
            flash("Invalid facility ID.", "danger")
        return redirect(url_for('admin_bp.manage_facilities'))

    return render_template('admin/manage_facilities.html', facilities=facilities)


# View booking analytics
@admin_bp.route('/analytics')
@login_required
@admin_required
def view_analytics():
    if not current_user.is_admin():
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for('main_bp.home'))

    # Example analytics: count reservations per facility
    analytics = db.session.query(
        Facility.name,
        db.func.count(Reservation.id).label('reservation_count')
    ).join(Reservation, Facility.id == Reservation.facility_id).group_by(Facility.name).all()

    return render_template('admin/analytics.html', analytics=analytics)
