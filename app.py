from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManger, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
import os

app = Flask(__name__)

# Database configuration moved here
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "your_secret_key"

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
jwt = JWTManger(app)

api = Api(app)

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': 'Username or Email already exists'}), 409
    
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(name=name, username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_has(user.password, password):
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 400
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'username': user.username,
        'email': user.email
    })

@app.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    return jsonify([book.to_dict() for book in books])

@app.route('/books', methods=['POST'])
@jwt_required()
def add_book():
    data = request.get_json()
    new_book = Book(
        title=data['title']
        author=data['author']
        description=data['description']
        price=data['price']
        stock=data['stock']
        category=data['category_id']
        image_url=data['image_url']
    )
    db.session.add(new_book)
    db.session.commit()
    return jsonify(new_book.to_dict()), 201

@app.route('/books/<int:book_id>', methods=['PUT'])
@jwt_required()
def edit_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    data = request.get_json()
    book.title = data['title']
    book.author = data['author']
    book.description = data['description']
    book.price = data['price']
    book.stock = data['stock']
    book.category = data['category']
    book.image_url = data['image_url']
    db.session.commit()

    return jsonify(book.to_dict())

@app.route('/books/<int:book_id', methods=['DELETE'])
@jwt_required()
def delete_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    db.session.delete(book)
    db.session.commit
    return jsonify({'message': 'Book deleted successfully'})

@app.route('/wishlist', methods=['POST'])
@jwt_required()
def add_to_wishlist():
    data = request.get_json()
    user_id = get_jwt_identity()
    book_id = data.get('book_id')


    wishlist_item = Wishlist(user_id=user_id, book_id=book_id)
    db.session.add(wishlist_item)
    db.session.commit()

    return jsonify({'message': 'Book added to Wishlist'}), 201

@app.route('/wishlist', methods=['GET'])
@jwt_required
def get_wishlist():
    user_id = get_jwt_identity()
    items = Wishlist.query.filter_by(user_id=user_id).all()
    return jsonify([item.to_dict() for item in items])

@app.route('/orders', methods=['POST'])
@jwt_required
def place_order():
    user_id = get_jwt_identity()
    data = request.get_json()

    new_order = Order(
        user_id=user_id,
        status='Pending',
        total_price=data['total_price']
        created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    db.session.add(new_order)
    db.session.commit()

    for item in data['items']:
        order_item = OrderItem(
            order_id=new_order.id,
            book_id=item['book_id'],
            quantity=item['quantity'],
            price=item['price']
        )
        db.session.add(new_order)

    db.session.commit()
    return jsonify({'message': 'Order placed successfully'}), 201

@app.route('/payments', methods=['POST'])
@jwt_required
def make_payment():
    data = request.get_json()
    order_id=data.get['order_id']
    payment_method=data.get['payment_method']
    transaction_id=data.get['transaction_id']

    new_payment = Payment(
        order_id=order_id,
        payment_method=payment_method,
        status='Completed',
        transaction_id=transaction_id,
        created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    db.session.add(new_payment)
    db.session.commit()

    return jsonify({'message': 'Payment done successfully'}), 201


if __name__ == "__main__":
    app.run(debug=True)
