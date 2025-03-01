from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import (
    JWTManager,
    get_jwt,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    create_refresh_token,
)
from flask_bcrypt import Bcrypt
from datetime import datetime
from flask_restful import Api
import os
from models import (
    db,
    User,
    Book,
    Order,
    OrderItem,
    Payment,
    Wishlist,
    Category,
    CartItem,
)
from functools import wraps


app = Flask(__name__)


# Database configuration moved here
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///TechReads.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "your_secret_key"


db.init_app(app)
CORS(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


api = Api(app)


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token is missing!"}), 400
        try:
            token = token.replace("Bearer ", "")
            user_id = get_jwt_identity()
            current_user = User.query.get(user_id)
            if not current_user:
                return jsonify({"message": "User not found!"}), 404
        except Exception as e:
            return jsonify({"message": str(e)}), 401
        return f(current_user, *args, **kwargs)

    return decorated_function


@app.route("/")
def home():
    return jsonify({"message": "Welcome to TechReads API!"})


@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    name = data.get("name")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Username or Email already exists"}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = User(name=name, username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if user:
        print(f"User found: {user.id}, {user.name}, {user.email}")

    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id, expires_delta=False)
        refresh_token = create_refresh_token(identity=user.id)

        return (
            jsonify(
                {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "name": user.name,
                        "email": user.email,
                        "id": user.id,
                    },
                }
            ),
            200,
        )

    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt().get("jti")
    return jsonify({"message": "Logged out successfully", "jti": jti}), 200


@app.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 400

    return jsonify(
        {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "email": user.email,
        }
    )


@app.route("/books", methods=["GET"])
@jwt_required()
def get_books():
    books = Book.query.all()
    return jsonify([book.to_dict() for book in books])


@app.route("/books", methods=["POST"])
@jwt_required()
def add_book():
    data = request.get_json()
    new_book = Book(
        title=data["title"],
        author=data["author"],
        description=data["description"],
        price=data["price"],
        stock=data["stock"],
        category_id=data["category_id"],
        image_url=data["image_url"],
    )
    db.session.add(new_book)
    db.session.commit()
    return jsonify(new_book.to_dict()), 201


@app.route("/books/<int:book_id>", methods=["PUT"])
@jwt_required()
def edit_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    data = request.get_json()
    book.title = data["title"]
    book.author = data["author"]
    book.description = data["description"]
    book.price = data["price"]
    book.stock = data["stock"]
    book.category_id = data["category_id"]
    book.image_url = data["image_url"]
    db.session.commit()

    return jsonify(book.to_dict())


@app.route("/books/<int:book_id>", methods=["DELETE"])
@jwt_required()
def delete_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    db.session.delete(book)
    db.session.commit()
    return jsonify({"message": "Book deleted successfully"})


@app.route("/wishlist/<int:book_id>", methods=["POST"])
@jwt_required()
def add_to_wishlist(book_id):
    user_id = get_jwt_identity()

    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    existing_item = Wishlist.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing_item:
        return jsonify({"message": "Book already in Wishlist"}), 200

    wishlist_item = Wishlist(user_id=user_id, book_id=book_id)
    db.session.add(wishlist_item)
    db.session.commit()

    return jsonify({"message": "Book added to Wishlist"}), 201


@app.route("/wishlist", methods=["GET"])
@jwt_required()
def get_wishlist():
    user_id = get_jwt_identity()
    items = Wishlist.query.filter_by(user_id=user_id).all()
    return jsonify([item.to_dict() for item in items])


@app.route("/cart/<int:book_id>", methods=["POST"])
@jwt_required()
def add_to_cart(book_id):
    user_id = get_jwt_identity()

    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    quantity = request.json.get("quantity", 1)

    existing_item = CartItem.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing_item:
        return jsonify({"message": "Book already in your cart"}), 200

    cart_item = CartItem(user_id=user_id, book_id=book_id, quantity=quantity)

    db.session.add(cart_item)
    db.session.commit()

    return jsonify({"message": "Book added to cart"}), 201


@app.route("/cart/<int:user_id>", methods=["GET"])
@jwt_required()
def get_cart(user_id):
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    return jsonify([item.to_dict() for item in cart_items]), 200

@app.route("/cart/<int:book_id>", methods=['PATCH'])
@jwt_required()
def update_cart_item(book_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    cart_item = CartItem.query.filter_by(user_id=user_id, book_id=book_id).first()

    if not cart_item:
        return jsonify({"error": 'Cart item not found'}), 404

    if "quantity" in data:
        new_quantity = data['"quantity']
        if new_quantity < 1:
            return jsonify({"error": "Quantity must be at least 1"}), 400
            
        cart_item.quantity = new_quantity

    db.session.commit()

    return jsonify({"message": "Cart updated successfully", "cart_item": cart_item.to_dict()}), 200



@app.route("/orders", methods=["GET"])
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()
    print("JWT Identity (user_id):", user_id)  # Debug print
    orders = (
        Order.query.filter_by(user_id=user_id).order_by(Order.datetime.desc()).all()
    )
    print("Orders fetched from DB:", orders)  # Debug print

    # Check if orders are being fetched correctly
    if not orders:
        print("No orders found for user_id:", user_id)  # Debug print

    return jsonify([order.to_dict() for order in orders]), 200


@app.route("/orders", methods=["POST"])
@jwt_required()
def place_order():
    user_id = get_jwt_identity()
    data = request.get_json()

    new_order = Order(
        user_id=user_id,
        status="Pending",
        total_price=data["total_price"],
        datetime=datetime.now(),
    )
    db.session.add(new_order)
    db.session.commit()

    items = data.get("items", [])
    if not items:
        return jsonify({"error": "No items provided"}), 400

    for item in items:
        if "book_id" not in item or "quantity" not in item or "price" not in item:
            return jsonify({"error": "Invalid item data"}), 400

    for item in items:
        order_item = OrderItem(
            order_id=new_order.id,
            book_id=item["book_id"],
            quantity=item["quantity"],
            price=item["price"],
        )
        db.session.add(order_item)

    db.session.commit()
    return jsonify({"message": "Order placed successfully"}), 201


@app.route("/payments", methods=["POST"])
@jwt_required()
def make_payment():
    data = request.get_json()
    order_id = data.get("order_id")
    payment_method = data.get("payment_method")
    transaction_id = data.get("transaction_id")

    new_payment = Payment(
        order_id=order_id,
        payment_method=payment_method,
        status="Completed",
        transaction_id=transaction_id,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    db.session.add(new_payment)
    db.session.commit()

    return jsonify({"message": "Payment done successfully"}), 201


@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    new_access_token = create_access_token(identity=identity, expires_delta=False)
    return jsonify({"access_token": new_access_token}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5555)
