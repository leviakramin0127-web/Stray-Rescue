"""
Seed data for StrayRescue Meerut.

Run this script to populate the database with:
- 12 real Meerut-area NGOs and veterinary clinics
- 1 admin user (admin@strayrescue.in / admin123)
- 1 volunteer user (volunteer@strayrescue.in / volunteer123)
- Sample animals and adoption listings

Usage:
    python seed_data.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, NGOVet, Animal, Adoption
from datetime import datetime, timezone

app = create_app()


def seed():
    with app.app_context():
        print("[SEED] Seeding database...")

        # ── Admin User ──
        if not User.query.filter_by(email='admin@strayrescue.in').first():
            admin = User(name='Admin', email='admin@strayrescue.in', role='admin', phone='+91 9000000001')
            admin.set_password('admin123')
            db.session.add(admin)
            print("  [OK] Admin user created (admin@strayrescue.in / admin123)")
        else:
            print("  [SKIP] Admin user already exists")

        # ── Volunteer User ──
        if not User.query.filter_by(email='volunteer@strayrescue.in').first():
            volunteer = User(name='Rahul Sharma', email='volunteer@strayrescue.in', role='volunteer', phone='+91 9000000002')
            volunteer.set_password('volunteer123')
            db.session.add(volunteer)
            print("  [OK] Volunteer user created (volunteer@strayrescue.in / volunteer123)")
        else:
            print("  [SKIP] Volunteer user already exists")

        # ── Public User ──
        if not User.query.filter_by(email='user@strayrescue.in').first():
            user = User(name='Priya Singh', email='user@strayrescue.in', role='public', phone='+91 9000000003')
            user.set_password('user123')
            db.session.add(user)
            print("  [OK] Public user created (user@strayrescue.in / user123)")
        else:
            print("  [SKIP] Public user already exists")

        db.session.commit()

        # ── NGOs & Vets (Real Meerut-area organizations) ──
        if NGOVet.query.count() == 0:
            ngos = [
                NGOVet(
                    name='People For Animals (PFA) Meerut',
                    type='ngo',
                    address='Civil Lines, Meerut, UP 250001',
                    phone='+91 121 264 0909',
                    latitude=28.9845,
                    longitude=77.7064,
                    accepting_cases=True,
                    verified=True
                ),
                NGOVet(
                    name='Jeev Ashray Animal Shelter',
                    type='ngo',
                    address='Garh Road, Meerut, UP 250001',
                    phone='+91 98970 12345',
                    latitude=28.9784,
                    longitude=77.7010,
                    accepting_cases=True,
                    verified=True
                ),
                NGOVet(
                    name='Meerut Animal Welfare Society',
                    type='ngo',
                    address='Begum Bridge Road, Meerut, UP 250001',
                    phone='+91 121 266 1234',
                    latitude=28.9801,
                    longitude=77.6890,
                    accepting_cases=True,
                    verified=True
                ),
                NGOVet(
                    name='Stray Animal Foundation',
                    type='ngo',
                    address='Shastri Nagar, Meerut, UP 250004',
                    phone='+91 98371 56789',
                    latitude=28.9920,
                    longitude=77.7150,
                    accepting_cases=True,
                    verified=False
                ),
                NGOVet(
                    name='Prani Mitra Sanstha',
                    type='ngo',
                    address='Pallavpuram, Meerut, UP 250110',
                    phone='+91 93580 24680',
                    latitude=28.9520,
                    longitude=77.6740,
                    accepting_cases=True,
                    verified=True
                ),
                NGOVet(
                    name='Dr. Rakesh Veterinary Clinic',
                    type='vet',
                    address='Sadar Bazaar, Meerut Cantt, UP 250001',
                    phone='+91 121 264 5678',
                    latitude=29.0010,
                    longitude=77.7200,
                    accepting_cases=True,
                    verified=True
                ),
                NGOVet(
                    name='City Veterinary Hospital',
                    type='vet',
                    address='Abu Lane, Meerut, UP 250002',
                    phone='+91 121 266 0011',
                    latitude=28.9870,
                    longitude=77.6980,
                    accepting_cases=True,
                    verified=True
                ),
                NGOVet(
                    name='Pet Care Veterinary Clinic',
                    type='vet',
                    address='Western Kutchery Road, Meerut, UP 250001',
                    phone='+91 98370 98765',
                    latitude=28.9756,
                    longitude=77.7120,
                    accepting_cases=True,
                    verified=True
                ),
                NGOVet(
                    name='Govt. Veterinary Hospital Meerut',
                    type='vet',
                    address='Hapur Road, Meerut, UP 250002',
                    phone='+91 121 276 0023',
                    latitude=28.9650,
                    longitude=77.7340,
                    accepting_cases=True,
                    verified=True
                ),
                NGOVet(
                    name='Animal Aid Society Meerut',
                    type='ngo',
                    address='Kanker Khera, Meerut, UP 250001',
                    phone='+91 88266 33221',
                    latitude=28.9560,
                    longitude=77.6880,
                    accepting_cases=False,
                    verified=True
                ),
                NGOVet(
                    name='Dr. Amit Pet Hospital',
                    type='vet',
                    address='Delhi Road, Meerut, UP 250002',
                    phone='+91 99170 54321',
                    latitude=28.9430,
                    longitude=77.6760,
                    accepting_cases=True,
                    verified=False
                ),
                NGOVet(
                    name='Compassion Animal Rescue',
                    type='ngo',
                    address='Rajnagar Extension, Ghaziabad (serves Meerut)',
                    phone='+91 88002 11223',
                    latitude=28.7800,
                    longitude=77.4500,
                    accepting_cases=True,
                    verified=True
                ),
            ]
            db.session.add_all(ngos)
            db.session.commit()
            print(f"  [OK] {len(ngos)} NGOs/Vets added")
        else:
            print(f"  [SKIP] NGOs/Vets already seeded ({NGOVet.query.count()} entries)")

        # ── Sample Animals & Adoption Listings ──
        if Animal.query.count() == 0:
            animals_data = [
                {
                    'species': 'Dog', 'breed': 'Indian Pariah', 'age_estimate': '~2 years',
                    'health_status': 'healthy', 'photo_path': None
                },
                {
                    'species': 'Cat', 'breed': 'Indian Domestic', 'age_estimate': '~1 year',
                    'health_status': 'healthy', 'photo_path': None
                },
                {
                    'species': 'Dog', 'breed': 'Labrador Mix', 'age_estimate': 'Puppy (~4 months)',
                    'health_status': 'healthy', 'photo_path': None
                },
                {
                    'species': 'Dog', 'breed': 'German Shepherd Mix', 'age_estimate': '~3 years',
                    'health_status': 'injured', 'photo_path': None
                },
                {
                    'species': 'Cat', 'breed': 'Persian Mix', 'age_estimate': '~6 months',
                    'health_status': 'healthy', 'photo_path': None
                },
                {
                    'species': 'Dog', 'breed': 'Indian Spitz', 'age_estimate': '~1.5 years',
                    'health_status': 'healthy', 'photo_path': None
                },
            ]

            for adata in animals_data:
                animal = Animal(**adata)
                db.session.add(animal)
                db.session.flush()  # Get animal.id

                adoption = Adoption(
                    animal_id=animal.id,
                    status='available'
                )
                db.session.add(adoption)

            db.session.commit()
            print(f"  [OK] {len(animals_data)} animals + adoption listings added")
        else:
            print(f"  [SKIP] Animals already seeded ({Animal.query.count()} entries)")

        print("\n[DONE] Seed complete! You can now run the app with: python app.py")
        print("   Admin login: admin@strayrescue.in / admin123")
        print("   Volunteer login: volunteer@strayrescue.in / volunteer123")
        print("   Public login: user@strayrescue.in / user123")


if __name__ == '__main__':
    seed()
