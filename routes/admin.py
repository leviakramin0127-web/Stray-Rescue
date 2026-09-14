from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Sighting, RescueCase, Adoption, User, NGOVet, Animal

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator that checks if current user is an admin."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    stats = {
        'total_sightings': Sighting.query.count(),
        'pending_sightings': Sighting.query.filter_by(status='pending').count(),
        'claimed_sightings': Sighting.query.filter_by(status='claimed').count(),
        'resolved_sightings': Sighting.query.filter_by(status='resolved').count(),
        'flagged_sightings': Sighting.query.filter_by(status='flagged').count(),
        'total_rescues': RescueCase.query.count(),
        'total_adoptions': Adoption.query.count(),
        'adopted_count': Adoption.query.filter_by(status='adopted').count(),
        'available_count': Adoption.query.filter_by(status='available').count(),
        'total_users': User.query.count(),
        'volunteers': User.query.filter_by(role='volunteer').count(),
        'total_ngos': NGOVet.query.count(),
    }

    flagged = Sighting.query.filter_by(status='flagged').order_by(Sighting.created_at.desc()).all()
    recent_sightings = Sighting.query.order_by(Sighting.created_at.desc()).limit(10).all()

    return render_template('admin_dashboard.html', stats=stats, flagged=flagged, recent_sightings=recent_sightings)


@admin_bp.route('/sighting/<int:sighting_id>/approve', methods=['POST'])
@admin_required
def approve_sighting(sighting_id):
    sighting = Sighting.query.get_or_404(sighting_id)
    sighting.status = 'pending'
    db.session.commit()
    flash(f'Sighting #{sighting.id} has been approved and set to pending.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/sighting/<int:sighting_id>/remove', methods=['POST'])
@admin_required
def remove_sighting(sighting_id):
    sighting = Sighting.query.get_or_404(sighting_id)
    db.session.delete(sighting)
    db.session.commit()
    flash(f'Sighting #{sighting_id} has been removed.', 'info')
    return redirect(url_for('admin.dashboard'))
