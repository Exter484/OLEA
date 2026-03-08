from app import app, db, User

def init_admin():
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin')
            admin.set_password('newpassword123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user 'admin' created with password 'newpassword123'")
        else:
            admin.set_password('newpassword123')
            db.session.commit()
            print("Admin user 'admin' password updated to 'newpassword123'")

if __name__ == "__main__":
    init_admin()
