from app import app, db
from models import User

with app.app_context():
    db.create_all()
    if not User.query.first():
        user1 = User(name="Alice")
        user2 = User(name="Bob")
        db.session.add_all([user1, user2])
        db.session.commit()
    print("Database seeded!")
