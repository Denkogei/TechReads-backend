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
    is_admin = db.Column(db.Boolean, default=False)


    orders = db.relationship('Order', backref='user', lazy=True)
    wishlist = db.relationship('Wishlist', backref='user', lazy=True)


    serialize_rules = ('-password', 'name', 'email', 'username', 'orders', 'wishlist')



    @validates('email')
    def validate_email(self, key, email):
        if '@' not in email:
            raise ValueError('Invalid email format')
        return email


    def __repr__(self):
        return f'<User {self.username}>, {self.email}>'


    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin 
        }




class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False) 
    price = db.Column(db.Float, nullable=False)       
    stock = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)

    order_items = db.relationship('OrderItem', backref='book', lazy=True)
    wishlist = db.relationship('Wishlist', backref='book', lazy=True)

    def __repr__(self):
        return f'<Book {self.title}, {self.author}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'description': self.description,
            'price': round(self.price, 2),  
            'stock': self.stock,
            'category_id': self.category_id,
            'image_url': self.image_url
        }




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


    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'total_price': self.total_price,
            'datetime': self.datetime
        }




class Wishlist(db.Model):
    __tablename__ = 'wishlist'


    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)


    def __repr__(self):
        return f'<Wishlist User:{self.user_id}>, Book:{self.book_id}>'


    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'title': self.book.title if self.book else None,
            'image_url': self.book.image_url if self.book else None,
            'price': self.book.price if self.book else None,
            'stock': self.book.stock if self.book else None
        }




class OrderItem(db.Model):
    __tablename__ = 'order_items'


    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)


    def __repr__(self):
        return f'<OrderItem Order:{self.order_id}>, Book:{self.book_id}>, Quantity: {self.quantity}>'


    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'book_id': self.book_id,
            'quantity': self.quantity,
            'price': self.price
        }




class Category(db.Model):
    __tablename__ = 'categories'


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


    books = db.relationship('Book', backref='book_category', lazy=True)


    def __repr__(self):
        return f'<Category {self.name}>'


    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }




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


    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'payment_method': self.payment_method,
            'amount': self.amount,
            'status': self.status,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at
        }


class CartItem(db.Model):
    __tablename__ = 'cart_items'


    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)


    user = db.relationship('User', backref='cart_items')
    book = db.relationship('Book', backref='cart_items')


    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'quantity': self.quantity,
            'book_title': self.book.title,
            'price': self.book.price,
            'image_url': self.book.image_url
        }
