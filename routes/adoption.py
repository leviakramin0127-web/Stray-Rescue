from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from models import db, Adoption, Animal

adoption_bp = Blueprint('adoption', __name__, url_prefix='/adoption')


@adoption_bp.route('/')
def list_adoptions():
    adoptions = (Adoption.query
                 .filter_by(status='available')
                 .order_by(Adoption.date_listed.desc())
                 .all())
    return render_template('adoption_list.html', adoptions=adoptions)


@adoption_bp.route('/<int:adoption_id>/apply', methods=['POST'])
@login_required
def apply_adoption(adoption_id):
    adoption = Adoption.query.get_or_404(adoption_id)
    if adoption.status != 'available':
        flash('This animal is no longer available for adoption.', 'info')
        return redirect(url_for('adoption.list_adoptions'))

    name = request.form.get('adopter_name', '').strip()
    contact = request.form.get('adopter_contact', '').strip()

    if not name or not contact:
        flash('Please provide your name and contact information.', 'danger')
        return redirect(url_for('adoption.list_adoptions'))

    adoption.adopter_name = name
    adoption.adopter_contact = contact
    adoption.status = 'pending'
    db.session.commit()

    flash('Your adoption interest has been submitted! We will contact you soon.', 'success')
    return redirect(url_for('adoption.list_adoptions'))
