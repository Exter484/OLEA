from app import app, db
import os

def reset():
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables with new schema...")
        db.create_all()
        print("Database reset successful.")

if __name__ == "__main__":
    reset()
