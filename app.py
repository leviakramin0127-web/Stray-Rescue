import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from config import Config
from models import db, User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload folder exists
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.sightings import sightings_bp
    from routes.ngo import ngo_bp
    from routes.adoption import adoption_bp
    from routes.admin import admin_bp
    from routes.profile import profile_bp
    from routes.foster import foster_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(sightings_bp)
    app.register_blueprint(ngo_bp)
    app.register_blueprint(adoption_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(foster_bp)

    # Home route
    @app.route('/')
    def index():
        from models import Sighting, Adoption, RescueCase
        stats = {
            'sightings': Sighting.query.count(),
            'rescues': RescueCase.query.filter(RescueCase.date_closed.isnot(None)).count(),
            'adoptions': Adoption.query.filter_by(status='adopted').count(),
        }
        return redirect(url_for('home'))

    @app.route('/home')
    def home():
        from flask import render_template
        from models import Sighting, Adoption, RescueCase, FosterParent, FosterAssignment
        stats = {
            'sightings': Sighting.query.count(),
            'rescues': RescueCase.query.filter(RescueCase.date_closed.isnot(None)).count(),
            'adoptions': Adoption.query.filter_by(status='adopted').count(),
            'fosters': FosterAssignment.query.filter_by(status='active').count(),
        }

        # Top 3 volunteers for mini leaderboard
        volunteers = User.query.filter(User.role.in_(['volunteer', 'admin'])).all()
        top_volunteers = []
        for v in volunteers:
            resolved = RescueCase.query.filter(
                RescueCase.volunteer_id == v.id,
                RescueCase.date_closed.isnot(None)
            ).count()
            top_volunteers.append({'user': v, 'resolved': resolved, 'badge': v.badge})
        top_volunteers.sort(key=lambda x: x['resolved'], reverse=True)
        top_volunteers = top_volunteers[:3]

        return render_template('index.html', stats=stats, top_volunteers=top_volunteers)

    # Create tables and seed data if empty
    with app.app_context():
        db.create_all()
        from models import User
        if User.query.count() == 0:
            try:
                from seed_data import seed
                seed(app)
            except Exception as e:
                print(f"Error seeding data: {e}")

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
