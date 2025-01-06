from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Facility, Reservation, db
from utility import admin_required
from datetime import datetime, timedelta

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
    if not current_user.is_admin:
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for('home_bp.home_page'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'make_all_available':
            Facility.query.update({Facility.is_available: True})
            db.session.commit()
            flash("All facilities have been made available.", "success")
        elif action == 'make_all_unavailable':
            Facility.query.update({Facility.is_available: False})
            db.session.commit()
            flash("All facilities have been made unavailable.", "success")
        elif action == 'toggle':
            facility_id = request.form.get('facility_id')
            facility = Facility.query.get(facility_id)
            if facility:
                facility.is_available = not facility.is_available
                db.session.commit()
                flash(f"Facility '{facility.name}' availability updated.", "success")

        return redirect(url_for('admin_bp.manage_facilities'))

    facilities = Facility.query.all()
    return render_template('admin/manage_facilities.html', facilities=facilities)

# View booking analytics
@admin_bp.route('/analytics')
@login_required
@admin_required
def view_analytics():
    if not current_user.is_admin:
        flash("Access denied! Admins only.", "danger")
        return redirect(url_for('home_bp.home_page'))

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = db.session.query(
        Facility.name,
        db.func.count(Reservation.id).label('reservation_count')
    ).join(Reservation, Facility.id == Reservation.facility_id)

    if start_date and end_date:
        try:
            query_start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query_end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include end date fully
            query = query.filter(Reservation.start_time >= query_start_date, Reservation.start_time < query_end_date)
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
            return redirect(url_for('admin_bp.view_analytics'))

    analytics = query.group_by(Facility.name).all()

    # Prepare data for the pie chart
    chart_labels = [facility for facility, _ in analytics]
    chart_values = [reservation_count for _, reservation_count in analytics]

    return render_template(
        'admin/analytics.html',
        analytics=analytics,
        start_date=start_date,
        end_date=end_date,
        chart_labels=chart_labels,
        chart_values=chart_values
    )
