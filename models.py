from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm import validates


db = SQLAlchemy()

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    orders = db.relationship('Order', backref='user', lazy=True)
    wishlist = db.relationship('Wishlist', backref='user', lazy=True)

    serialize_rules = ('-password', 'orders.user', 'wishlist.user')

    @validates('email')
    def validate_email(self, key, email):
        if '@' not in email:
            raise ValueError('Invalid email format')
        return email

    def __repr__(self):
        return f'<User {self.username}>, {self.email}>'


class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    decsription = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(100), db.ForeignKey('categories.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)

    order_items = db.relationship('OrderItem', backref='book', lazy=True)
    wishlist = db.relationship('Wishlist', backref='book', lazy=True)

    def __repr__(self):
        return f'<Book {self.title}>, {self.author}>'


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(100), nullable=False)
    total_price = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)

    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    payment = db.relationship('Payment', backref='order', lazy=True)

    def __repr__(self):
        return f'<Order {self.id}>, {self.user_id}>, Status: {self.status} Total Price: {self.total_price}>'
    

class Wishlist(db.Model):
    __tablename__ = 'wishlist'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)

    def __repr__(self):
        return f'<Wishlist User:{self.user_id}>, Book:{self.book_id}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<OrderItem Order:{self.order_id}>, Book:{self.book_id}>, Quantity: {self.quantity}>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    books = db.relationship('Book', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'
    

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    payment_method = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(100), nullable=False)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<Payment Order:{self.order_id}>, Status: {self.status}>, Transaction: {self.transaction_id}>"