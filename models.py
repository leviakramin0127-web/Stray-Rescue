from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='public')  # public / volunteer / admin
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    sightings = db.relationship('Sighting', backref='reporter', lazy='dynamic')
    rescue_cases = db.relationship('RescueCase', backref='volunteer', lazy='dynamic')
    foster_profile = db.relationship('FosterParent', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def rescue_count(self):
        """Number of rescue cases this user has resolved."""
        return RescueCase.query.filter(
            RescueCase.volunteer_id == self.id,
            RescueCase.date_closed.isnot(None)
        ).count()

    @property
    def claimed_count(self):
        """Number of rescue cases this user has claimed (total)."""
        return RescueCase.query.filter_by(volunteer_id=self.id).count()

    @property
    def active_fosters_count(self):
        """Number of animals currently being fostered by this user."""
        if not self.foster_profile:
            return 0
        return FosterAssignment.query.filter(
            FosterAssignment.foster_parent_id == self.foster_profile.id,
            FosterAssignment.status == 'active'
        ).count()

    @property
    def total_fosters_count(self):
        """Total number of animals this user has fostered."""
        if not self.foster_profile:
            return 0
        return FosterAssignment.query.filter(
            FosterAssignment.foster_parent_id == self.foster_profile.id
        ).count()

    @property
    def badge(self):
        """Return the user's impact badge based on rescue count."""
        count = self.rescue_count
        if count >= 10:
            return {'name': 'Hero', 'icon': 'bi-trophy-fill', 'color': '#f59e0b', 'tier': 'gold'}
        elif count >= 5:
            return {'name': 'Guardian', 'icon': 'bi-shield-fill-check', 'color': '#94a3b8', 'tier': 'silver'}
        elif count >= 1:
            return {'name': 'First Responder', 'icon': 'bi-star-fill', 'color': '#cd7f32', 'tier': 'bronze'}
        return None

    def __repr__(self):
        return f'<User {self.name} ({self.role})>'


class NGOVet(db.Model):
    __tablename__ = 'ngo_vet'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # ngo / vet
    address = db.Column(db.String(300))
    phone = db.Column(db.String(20))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accepting_cases = db.Column(db.Boolean, default=True)
    verified = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<NGOVet {self.name} ({self.type})>'


class Animal(db.Model):
    __tablename__ = 'animals'

    id = db.Column(db.Integer, primary_key=True)
    species = db.Column(db.String(50), nullable=False)  # dog / cat / bird / other
    breed = db.Column(db.String(100))
    age_estimate = db.Column(db.String(50))  # e.g. "~2 years", "puppy"
    health_status = db.Column(db.String(50), default='unknown')  # healthy / injured / sick / unknown
    photo_path = db.Column(db.String(300))

    # Relationships
    vaccinations = db.relationship('VaccinationRecord', backref='animal', lazy='dynamic')
    adoption = db.relationship('Adoption', backref='animal', uselist=False)

    def __repr__(self):
        return f'<Animal {self.species} – {self.breed}>'


class Sighting(db.Model):
    __tablename__ = 'sightings'

    id = db.Column(db.Integer, primary_key=True)
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    species_guess = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    photo_path = db.Column(db.String(300))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending / claimed / resolved / flagged
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    rescue_case = db.relationship('RescueCase', backref='sighting', uselist=False)

    def __repr__(self):
        return f'<Sighting #{self.id} – {self.species_guess} ({self.status})>'


class RescueCase(db.Model):
    __tablename__ = 'rescue_cases'

    id = db.Column(db.Integer, primary_key=True)
    sighting_id = db.Column(db.Integer, db.ForeignKey('sightings.id'), nullable=False)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_taken = db.Column(db.Text)
    date_claimed = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date_closed = db.Column(db.DateTime)

    def __repr__(self):
        return f'<RescueCase #{self.id} for Sighting #{self.sighting_id}>'


class VaccinationRecord(db.Model):
    __tablename__ = 'vaccination_records'

    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id'), nullable=False)
    vaccine_name = db.Column(db.String(100), nullable=False)
    date_given = db.Column(db.Date, nullable=False)
    next_due = db.Column(db.Date)

    def __repr__(self):
        return f'<Vaccination {self.vaccine_name} for Animal #{self.animal_id}>'


class Adoption(db.Model):
    __tablename__ = 'adoptions'

    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id'), nullable=False)
    adopter_name = db.Column(db.String(120))
    adopter_contact = db.Column(db.String(120))
    status = db.Column(db.String(20), default='available')  # available / pending / adopted
    date_listed = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Adoption #{self.id} – {self.status}>'


class FosterParent(db.Model):
    __tablename__ = 'foster_parents'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    animal_types = db.Column(db.String(200), nullable=False)  # comma-separated: "dog,cat,bird"
    max_animals = db.Column(db.Integer, default=1)
    has_outdoor_space = db.Column(db.Boolean, default=False)
    experience_notes = db.Column(db.Text)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    assignments = db.relationship('FosterAssignment', backref='foster_parent', lazy='dynamic')

    @property
    def active_count(self):
        return self.assignments.filter_by(status='active').count()

    @property
    def can_take_more(self):
        return self.is_available and self.active_count < self.max_animals

    def __repr__(self):
        return f'<FosterParent {self.user.name}>'


class FosterAssignment(db.Model):
    __tablename__ = 'foster_assignments'

    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id'), nullable=False)
    foster_parent_id = db.Column(db.Integer, db.ForeignKey('foster_parents.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # active / completed / cancelled
    start_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    end_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)

    # Relationships
    animal = db.relationship('Animal', backref='foster_assignment')
    assigner = db.relationship('User', foreign_keys=[assigned_by])

    def __repr__(self):
        return f'<FosterAssignment #{self.id} – {self.status}>'
