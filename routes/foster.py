from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Animal, FosterParent, FosterAssignment

foster_bp = Blueprint('foster', __name__, url_prefix='/foster')


@foster_bp.route('/')
def foster_home():
    """Foster program overview — animals needing foster + available foster parents."""
    # Animals that need foster (not currently fostered, not adopted)
    # Find animals with no active foster assignment
    fostered_animal_ids = [a.animal_id for a in
                           FosterAssignment.query.filter_by(status='active').all()]
    animals_needing_foster = (Animal.query
                              .filter(Animal.id.notin_(fostered_animal_ids) if fostered_animal_ids else Animal.id.isnot(None))
                              .all())

    # Available foster parents who can take more
    all_fosters = FosterParent.query.filter_by(is_available=True).all()
    available_fosters = [f for f in all_fosters if f.can_take_more]

    # Active foster assignments
    active_assignments = (FosterAssignment.query
                          .filter_by(status='active')
                          .order_by(FosterAssignment.start_date.desc())
                          .all())

    return render_template('foster_list.html',
                           animals_needing=animals_needing_foster,
                           available_fosters=available_fosters,
                           active_assignments=active_assignments)


@foster_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Register as a foster parent."""
    # Check if already registered
    existing = FosterParent.query.filter_by(user_id=current_user.id).first()
    if existing:
        flash('You are already registered as a foster parent!', 'info')
        return redirect(url_for('foster.foster_home'))

    if request.method == 'POST':
        animal_types = request.form.getlist('animal_types')
        max_animals = request.form.get('max_animals', 1, type=int)
        has_outdoor = 'has_outdoor_space' in request.form
        experience = request.form.get('experience_notes', '').strip()

        if not animal_types:
            flash('Please select at least one animal type you can foster.', 'danger')
            return render_template('foster_register.html')

        if max_animals < 1 or max_animals > 10:
            max_animals = 1

        foster = FosterParent(
            user_id=current_user.id,
            animal_types=','.join(animal_types),
            max_animals=max_animals,
            has_outdoor_space=has_outdoor,
            experience_notes=experience,
            is_available=True
        )
        db.session.add(foster)

        # Upgrade role to volunteer if they're a public user
        if current_user.role == 'public':
            current_user.role = 'volunteer'

        db.session.commit()

        flash('You are now registered as a foster parent! Thank you for opening your home.', 'success')
        return redirect(url_for('foster.foster_home'))

    return render_template('foster_register.html')


@foster_bp.route('/my')
@login_required
def my_fosters():
    """View my active and past foster assignments."""
    if not current_user.foster_profile:
        flash('You are not registered as a foster parent yet.', 'info')
        return redirect(url_for('foster.register'))

    active = (FosterAssignment.query
              .filter_by(foster_parent_id=current_user.foster_profile.id, status='active')
              .order_by(FosterAssignment.start_date.desc())
              .all())
    completed = (FosterAssignment.query
                 .filter_by(foster_parent_id=current_user.foster_profile.id, status='completed')
                 .order_by(FosterAssignment.end_date.desc())
                 .all())

    return render_template('foster_my.html', active=active, completed=completed)


@foster_bp.route('/assign', methods=['POST'])
@login_required
def assign_animal():
    """Admin assigns an animal to a foster parent."""
    if current_user.role != 'admin':
        flash('Only admins can assign foster animals.', 'danger')
        return redirect(url_for('foster.foster_home'))

    animal_id = request.form.get('animal_id', type=int)
    foster_parent_id = request.form.get('foster_parent_id', type=int)
    notes = request.form.get('notes', '').strip()

    if not animal_id or not foster_parent_id:
        flash('Please select both an animal and a foster parent.', 'danger')
        return redirect(url_for('foster.foster_home'))

    animal = Animal.query.get_or_404(animal_id)
    foster_parent = FosterParent.query.get_or_404(foster_parent_id)

    if not foster_parent.can_take_more:
        flash(f'{foster_parent.user.name} cannot take more animals right now.', 'warning')
        return redirect(url_for('foster.foster_home'))

    # Check if animal is already being fostered
    existing = FosterAssignment.query.filter_by(animal_id=animal_id, status='active').first()
    if existing:
        flash('This animal is already being fostered.', 'info')
        return redirect(url_for('foster.foster_home'))

    assignment = FosterAssignment(
        animal_id=animal_id,
        foster_parent_id=foster_parent_id,
        assigned_by=current_user.id,
        notes=notes
    )
    db.session.add(assignment)
    db.session.commit()

    flash(f'{animal.species} has been assigned to {foster_parent.user.name} for fostering!', 'success')
    return redirect(url_for('foster.foster_home'))


@foster_bp.route('/assignment/<int:assignment_id>/complete', methods=['POST'])
@login_required
def complete_assignment(assignment_id):
    """Mark a foster assignment as completed (animal found permanent home)."""
    assignment = FosterAssignment.query.get_or_404(assignment_id)

    # Only admin or the foster parent themselves can complete
    is_foster_owner = (current_user.foster_profile and
                       current_user.foster_profile.id == assignment.foster_parent_id)
    if current_user.role != 'admin' and not is_foster_owner:
        flash('Access denied.', 'danger')
        return redirect(url_for('foster.foster_home'))

    assignment.status = 'completed'
    assignment.end_date = datetime.now(timezone.utc)
    db.session.commit()

    flash('Foster assignment completed! The animal has found a permanent home.', 'success')
    return redirect(url_for('foster.foster_home'))


@foster_bp.route('/toggle-availability', methods=['POST'])
@login_required
def toggle_availability():
    """Toggle foster parent availability."""
    if not current_user.foster_profile:
        flash('You are not registered as a foster parent.', 'warning')
        return redirect(url_for('foster.register'))

    current_user.foster_profile.is_available = not current_user.foster_profile.is_available
    db.session.commit()

    status = 'available' if current_user.foster_profile.is_available else 'unavailable'
    flash(f'Your foster status is now: {status}', 'info')
    return redirect(url_for('foster.my_fosters'))
