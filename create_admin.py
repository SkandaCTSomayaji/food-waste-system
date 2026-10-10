import getpass
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    email = input("Admin email: ").strip().lower()
    if User.query.filter_by(email=email).first():
        print("That email already exists.")
        raise SystemExit

    admin = User(name="Admin", email=email, role="admin")
    admin.set_password(getpass.getpass("Password: "))
    db.session.add(admin)
    db.session.commit()
    print("Admin created.")