from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, RescueCase, FosterParent, FosterAssignment

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile')
@login_required
def my_profile():
    """Redirect logged-in user to their own profile."""
    return redirect(url_for('profile.view_profile', user_id=current_user.id))


@profile_bp.route('/profile/<int:user_id>')
def view_profile(user_id):
    """View a user's public profile with rescue stats and badges."""
    user = User.query.get_or_404(user_id)

    # Rescue timeline — all resolved cases by this user
    resolved_cases = (RescueCase.query
                      .filter_by(volunteer_id=user.id)
                      .filter(RescueCase.date_closed.isnot(None))
                      .order_by(RescueCase.date_closed.desc())
                      .all())

    # Active foster assignments
    active_fosters = []
    completed_fosters = []
    if user.foster_profile:
        active_fosters = (FosterAssignment.query
                          .filter_by(foster_parent_id=user.foster_profile.id, status='active')
                          .order_by(FosterAssignment.start_date.desc())
                          .all())
        completed_fosters = (FosterAssignment.query
                             .filter_by(foster_parent_id=user.foster_profile.id, status='completed')
                             .order_by(FosterAssignment.end_date.desc())
                             .all())

    return render_template('profile.html',
                           profile_user=user,
                           resolved_cases=resolved_cases,
                           active_fosters=active_fosters,
                           completed_fosters=completed_fosters)


@profile_bp.route('/volunteers/leaderboard')
def leaderboard():
    """Volunteer leaderboard — ranked by resolved rescue cases."""
    # Get all volunteers and admins
    volunteers = User.query.filter(User.role.in_(['volunteer', 'admin'])).all()

    # Build leaderboard data
    board = []
    for v in volunteers:
        resolved = RescueCase.query.filter(
            RescueCase.volunteer_id == v.id,
            RescueCase.date_closed.isnot(None)
        ).count()
        claimed = RescueCase.query.filter_by(volunteer_id=v.id).count()
        fosters = v.total_fosters_count

        board.append({
            'user': v,
            'resolved': resolved,
            'claimed': claimed,
            'fosters': fosters,
            'total_impact': resolved + fosters,  # Combined score
            'badge': v.badge
        })

    # Sort by total_impact descending
    board.sort(key=lambda x: x['total_impact'], reverse=True)

    return render_template('leaderboard.html', board=board)
