from flask_sqlalchemy import SQLAlchemy
from sqialchemy_serializer import SerializerMixin
from sqlalchemy.orm import validates

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    orders = db.relationship('Order', backref='user', lazy=True)
    wishlist = db.relationship('Wishlist', backref='user', lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name}

class Book(db.Model):
    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    decsription = db.Column(db.String(200), nullable=False)
    price = db.Column(db.integer, nullable=False)
    stock = db.Column(db.integer, nullable=False)
    category = db.Column(db.String(100), db.Foreignkey('categories.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)

    order_items = db.relationship('OrderItem', backref='book', lazy=True)
    wishlist = db.relationship('Wishlist', backref='book', lazy=True)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "author": self.author}
    
class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(100), nullable=False)
    total_price = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)

    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    payment = db.relationship('Payment', backref='order', lazy=True)

    def to_dict(self):
        return {"id": self.id, "user_id": self.user_id, "book_id": self.book_id}
    
class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)

    def to_dict(self):
        return {"id": self.id, "user_id": self.user_id, "book_id": self.book_id}

class OrderItem(db.model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {"id": self.id, "order_id": self.order_id, "book_id": self.book_id, "quantity": self.quantity, "price": self.price}

class Payment(db.model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    payment_method = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(100), nullable=False)

