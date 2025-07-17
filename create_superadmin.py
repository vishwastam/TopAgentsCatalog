import sys
import os
import uuid
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app import create_app
from models import db, User

if len(sys.argv) != 3:
    print("Usage: python create_superadmin.py <email> <password>")
    sys.exit(1)

email = sys.argv[1]
password = sys.argv[2]

app = create_app()

with app.app_context():
    if User.query.filter_by(email=email).first():
        print(f"User with email {email} already exists.")
        sys.exit(1)
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        full_name="Super Admin",
        first_name="Super",
        last_name="Admin",
        password_hash=generate_password_hash(password),
        role='superadmin',
        primary_role='superadmin',
        roles=['superadmin', 'admin'],
        status='active'
    )
    db.session.add(user)
    db.session.commit()
    print(f"Superadmin user {email} created successfully.") 