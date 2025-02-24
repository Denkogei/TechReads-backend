from faker import Faker
from app import app, db
from models import User, Book, Category
from datetime import datetime
import random

fake = Faker()

def seed_data():
    with app.app_context():
        print("Dropping old data...")
        db.drop_all()
        db.create_all()

        users = []
        for _ in range(10):
            user = User(
                name=fake.name(),
                username=fake.user_name(),
                email=fake.email(),
                password='password'
            )
            users.append(user)
            db.session.add(user)
        db.session.commit()
        print("Seeded users")

        category_names = ['Programming', 'Software Architecture', 'Web Development', 'Data Science', 'Artificial Intelligence', 'Cybersecurity', 'DevOps']
        categories = []
        for name in category_names:
            category = Category(name=name)
            categories.append(category)
            db.session.add(category)
        db.session.commit()
        print("Categories seeded!")

        books = []
        for _ in range(50):
            book = Book(
                title=fake.sentence(),
                author=fake.name(),
                description=fake.text(),
                price=random.randint(10, 100),
                stock=random.randint(0, 100),
                category_id=random.choice(categories).id,
                image_url=fake.image_url()
            )
            books.append(book)
            db.session.add(book)
        db.session.commit()
        print("Books seeded!")

        orders = []
        for _ in range(20):
            order = Order(
                user_idrandom.choice(users).id,
                status=random.choice(['Pending', 'Shipped', 'Delivered']),
                total_price=random.randint(1000, 10000),
                datetime=fake.date_time()
            )
            orders.append(order)
            db.session.add(order)
        db.session.commit()
        print("Orders seeded!")

        print("Database seeding completed!")

if __name__ == '__main__':
    seed_data()