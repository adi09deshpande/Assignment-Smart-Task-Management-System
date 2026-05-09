"""
One-time database setup script.
Run once after configuring your .env file:
    python init_db.py
"""
from app import create_app, db

app = create_app()

with app.app_context():
    db.create_all()
    print("Database tables created successfully.")
