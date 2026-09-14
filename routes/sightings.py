import os
import uuid
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db, Sighting, RescueCase

sightings_bp = Blueprint('sightings', __name__, url_prefix='/sightings')


def save_upload(file):
    """Save an uploaded file and return the relative path."""
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
            return None
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return f"uploads/{filename}"
    return None


@sightings_bp.route('/')
def list_sightings():
    status_filter = request.args.get('status', 'all')
    query = Sighting.query.order_by(Sighting.created_at.desc())
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    sightings = query.all()
    return render_template('sightings_list.html', sightings=sightings, current_filter=status_filter)


@sightings_bp.route('/report', methods=['GET', 'POST'])
@login_required
def report_sighting():
    if request.method == 'POST':
        species = request.form.get('species_guess', '').strip()
        description = request.form.get('description', '').strip()
        latitude = request.form.get('latitude', '')
        longitude = request.form.get('longitude', '')

        if not species or not latitude or not longitude:
            flash('Please provide species and allow location access.', 'danger')
            return render_template('report_sighting.html')

        try:
            lat = float(latitude)
            lon = float(longitude)
        except ValueError:
            flash('Invalid location data.', 'danger')
            return render_template('report_sighting.html')

        photo_path = None
        if 'photo' in request.files:
            photo_path = save_upload(request.files['photo'])

        sighting = Sighting(
            reported_by=current_user.id,
            species_guess=species,
            description=description,
            photo_path=photo_path,
            latitude=lat,
            longitude=lon,
            status='pending'
        )
        db.session.add(sighting)
        db.session.commit()

        flash('Sighting reported successfully! Volunteers will be notified.', 'success')
        return redirect(url_for('sightings.list_sightings'))

    return render_template('report_sighting.html')


@sightings_bp.route('/<int:sighting_id>/claim', methods=['POST'])
@login_required
def claim_sighting(sighting_id):
    if current_user.role not in ('volunteer', 'admin'):
        flash('Only volunteers can claim sightings.', 'warning')
        return redirect(url_for('sightings.list_sightings'))

    sighting = Sighting.query.get_or_404(sighting_id)
    if sighting.status != 'pending':
        flash('This sighting has already been claimed or resolved.', 'info')
        return redirect(url_for('sightings.list_sightings'))

    sighting.status = 'claimed'
    rescue = RescueCase(
        sighting_id=sighting.id,
        volunteer_id=current_user.id
    )
    db.session.add(rescue)
    db.session.commit()

    flash(f'You have claimed sighting #{sighting.id}. Please take action!', 'success')
    return redirect(url_for('sightings.list_sightings'))


@sightings_bp.route('/<int:sighting_id>/resolve', methods=['POST'])
@login_required
def resolve_sighting(sighting_id):
    sighting = Sighting.query.get_or_404(sighting_id)
    rescue = RescueCase.query.filter_by(sighting_id=sighting.id).first()

    if not rescue or rescue.volunteer_id != current_user.id:
        if current_user.role != 'admin':
            flash('Only the assigned volunteer or an admin can resolve this.', 'warning')
            return redirect(url_for('sightings.list_sightings'))

    action = request.form.get('action_taken', '').strip()
    sighting.status = 'resolved'
    if rescue:
        rescue.action_taken = action
        rescue.date_closed = datetime.now(timezone.utc)
    db.session.commit()

    flash(f'Sighting #{sighting.id} marked as resolved. Thank you!', 'success')
    return redirect(url_for('sightings.list_sightings'))


@sightings_bp.route('/<int:sighting_id>/flag', methods=['POST'])
@login_required
def flag_sighting(sighting_id):
    sighting = Sighting.query.get_or_404(sighting_id)
    sighting.status = 'flagged'
    db.session.commit()
    flash('Sighting has been flagged for admin review.', 'warning')
    return redirect(url_for('sightings.list_sightings'))
