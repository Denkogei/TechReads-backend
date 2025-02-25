from faker import Faker
from app import app, db
from models import User, Book, Category, Order, OrderItem
from datetime import datetime
import random

fake = Faker()

book_data = [
    ("Clean Code", "Robert C. Martin", "A Handbook of Agile Software Craftsmanship."),
    ("The Pragmatic Programmer", "Andrew Hunt & David Thomas", "Classic software development book covering best practices."),
    ("You Don't Know JS", "Kyle Simpson", "Deep dive into JavaScript, closures, scope, and event loop."),
    ("Design Patterns", "Erich Gamma et al.", "Elements of reusable object-oriented software."),
    ("Python Crash Course", "Eric Matthes", "Fast-paced introduction to Python programming."),
    ("Artificial Intelligence: A Guide", "Stuart Russell & Peter Norvig", "Covers AI concepts, machine learning, and neural networks."),
    ("Data Science from Scratch", "Joel Grus", "Beginner-friendly introduction to data science concepts."),
    ("Web Development with Django", "William S. Vincent", "Comprehensive guide to building web apps using Django."),
    ("Cybersecurity Essentials", "Charles J. Brooks", "Key principles of cybersecurity and ethical hacking."),
    ("Site Reliability Engineering", "Google SRE Team", "Insights from Google engineers on DevOps and scalability."),
    ("Fluent Python", "Luciano Ramalho", "Advanced Python programming techniques and best practices."),
    ("Deep Learning with Python", "François Chollet", "Neural networks, deep learning, and AI applications."),
    ("React & Redux", "Mark T. Smith", "Modern front-end development with React and Redux."),
    ("JavaScript: The Good Parts", "Douglas Crockford", "Essential guide to writing clean JavaScript."),
    ("Building Microservices", "Sam Newman", "Scalable service-based architecture for software systems."),
]

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

        category_names = ['Programming', 'Software Architecture', 'Web Development', 'Data Science', 'Artificial Intelligence', 'Cybersecurity', 'DevOps']
        categories = []
        for name in category_names:
            category = Category(name=name)
            categories.append(category)
            db.session.add(category)
        db.session.commit()

        books = []
        for title, author, description in book_data:
            stock = random.randint(0, 50)
            book = Book(
                title=title,
                author=author,
                description=description,
                price=random.randint(1500, 15000),
                stock=random.randint(5, 50),
                category_id=random.choice(categories).id,
                image_url=fake.image_url(),
                rating=(random.uniform(1.0, 5.0), 1),
                out_of_stock=(stock == 0)
            )
            books.append(book)
            db.session.add(book)
        db.session.commit()

        orders = []
        for _ in range(20):
            order = Order(
                user_id=random.choice(users).id,
                status=random.choice(['Pending', 'Shipped', 'Delivered']),
                total_price=random.randint(5000, 50000),
                datetime=fake.date_time()
            )
            orders.append(order)
            db.session.add(order)
        db.session.commit()

        order_items = []
        for order in orders:
            for _ in range(random.randint(1, 5)):
                order_item = OrderItem(
                    order_id=order.id,
                    book_id=random.choice(books).id,
                    quantity=random.randint(1, 5),
                    price=book.price
                )
                order_items.append(order_item)
                db.session.add(order_item)
        db.session.commit()

        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_data()