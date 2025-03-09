from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, get_jwt, create_access_token, jwt_required, get_jwt_identity, create_refresh_token
from flask_bcrypt import Bcrypt
from datetime import datetime
from flask_restful import Api
import os
from models import db, User, Book, Order, OrderItem, Payment, Wishlist, Category, CartItem
from functools import wraps
import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
import os
load_dotenv()
app = Flask(__name__)

# Database configuration moved here
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "your_secret_key"



db.init_app(app)
CORS(app, resources={r"/*": {"origins": ["http://127.0.0.1:5173", "https://techreadsafrica.netlify.app" "http://localhost:5173"]}})




SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_SENDER_EMAIL = os.getenv("SENDGRID_SENDER_EMAIL")

migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

api = Api(app)


cloudinary.config(
    cloud_name="dklgssxtk",
    api_key="335984976478135",
    api_secret="sOCQeXSIKcrlx3IRM_tOeVn-mrI"
)


def get_mpesa_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    
    consumer_key = "DGnrLBUtUoke80CT6aFwD9hmVmTpT6ArW0vVxAmbekm2ApGn"
    consumer_secret = "88JoyDdIwn41HDixfeZqoQL3yMl9FGv6m5FtOZAqtFqWNE5XuA9d3GeaAP8h3erK"
    
    auth_string = f"{consumer_key}:{consumer_secret}"
    auth_encoded = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_encoded}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    response_json = response.json()
    return response_json.get("access_token")


@app.route('/mpesa/stkpush', methods=['POST'])
def mpesa_stkpush():
    
    MPESA_CONSUMER_KEY = "DGnrLBUtUoke80CT6aFwD9hmVmTpT6ArW0vVxAmbekm2ApGn"
    MPESA_CONSUMER_SECRET = "88JoyDdIwn41HDixfeZqoQL3yMl9FGv6m5FtOZAqtFqWNE5XuA9d3GeaAP8h3erK"
    MPESA_SHORTCODE = "174379"
    MPESA_PASSKEY = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
    MPESA_BASE_URL = "https://sandbox.safaricom.co.ke"
    CALLBACK_URL = "https://techreads-backend.onrender.com/mpesa/callback"

    
    data = request.get_json()
    phone_number = data.get("phone_number")
    amount = data.get("amount")
    order_id = data.get("order_id")

    
    if not phone_number or not amount or not order_id:
         return jsonify({"error": "Missing required fields"}), 400

    
    auth_url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    auth_response = requests.get(auth_url, auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET))
    access_token = auth_response.json().get("access_token")

    if not access_token:
        return jsonify({"error": "Failed to get access token"}), 400

    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}".encode()).decode()

    
    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": str(order_id),
        "TransactionDesc": "Payment for TechReads Order"
    }

    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest", json=payload, headers=headers)

    
    if response.status_code == 200:
        return response.json()
    else:
        return jsonify({"error": f"{response.status_code} {response.reason}", "details": response.text}), 400



@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()
    print("Mpesa Callback Data:", data)

    if not data:
        return jsonify({"error": "Invalid callback data"}), 400

    stk_callback = data.get("Body", {}).get("stkCallback", {})
    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc")
    metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])

    print("STK Callback Parsed:", stk_callback)
    print("Metadata:", metadata)

    
    if result_code == 0:
        
        payment_details = {item["Name"]: item.get("Value") for item in metadata}
        transaction_id = payment_details.get("MpesaReceiptNumber")
        amount = payment_details.get("Amount")

        if not transaction_id:
            print("Missing transaction_id")
            return jsonify({"error": "Missing payment details"}), 400

        
        try:
            amount = int(float(amount))
        except ValueError:
            return jsonify({"error": "Invalid amount"}), 400

        
        new_order = Order(
            user_id=1,  
            status="Paid",
            total_price=amount,
            datetime=datetime.now()
        )
        db.session.add(new_order)
        db.session.commit()

        
        new_payment = Payment(
            order_id=new_order.id,
            payment_method="Mpesa",
            amount=amount,  
            status="Completed",
            transaction_id=transaction_id,
            created_at=datetime.now()
        )
        db.session.add(new_payment)
        db.session.commit()

        
        return jsonify({"message": "Payment successful", "transaction_id": transaction_id}), 200

    return jsonify({"error": "Payment failed", "description": result_desc}), 400


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
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


@app.route('/')
def home():
    return jsonify({"message": "Welcome to TechReads API!"})


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

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    
    print(f"Stored password hash: {user.password}")

    try:
        if bcrypt.check_password_hash(user.password, password):
            access_token = create_access_token(identity=user.id, expires_delta=False)
            refresh_token = create_refresh_token(identity=user.id)

            return jsonify({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'name': user.name,
                    'email': user.email,
                    'id': user.id,
                }
            }), 200
    except ValueError:
        return jsonify({'error': 'Invalid password format. Please reset your password.'}), 500

    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt().get("jti")
    return jsonify({'message': 'Logged out successfully', 'jti': jti}), 200


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
@jwt_required()
def get_books():
    books = Book.query.all()
    return jsonify([book.to_dict() for book in books])


@app.route('/books/<int:id>', methods=['GET'])
@jwt_required()
def get_book_by_id(id):
    book = Book.query.get_or_404(id)  
    return jsonify(book.to_dict())  


@app.route('/books', methods=['POST'])
@jwt_required()
def add_book():
    data = request.get_json()
   
    
    required_fields = ['title', 'author', 'price', 'stock', 'category_id', 'image_url']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({
            "error": "Missing required fields",
            "missing": missing_fields
        }), 400


    try:
        if 'cloudinary.com' not in data['image_url']:
            return jsonify({
                "error": "Invalid image URL format",
                "details": "Must be a valid Cloudinary URL"
            }), 400


        numeric_fields = {
            'price': (float, 'Price must be a positive number'),
            'stock': (int, 'Stock must be a non-negative integer'),
            'category_id': (int, 'Category ID must be an integer')
        }
       
        validated = {}
        for field, (converter, error_msg) in numeric_fields.items():
            try:
                value = converter(data[field])
                if field in ['price'] and value <= 0:
                    raise ValueError(error_msg)
                if field == 'stock' and value < 0:
                    raise ValueError(error_msg)
                validated[field] = value
            except (ValueError, TypeError):
                return jsonify({
                    "error": "Validation error",
                    "field": field,
                    "message": error_msg
                }), 400


        if not Category.query.get(validated['category_id']):
            return jsonify({
                "error": "Invalid category",
                "message": "Specified category does not exist"
            }), 400


        new_book = Book(
            title=data['title'].strip(),
            author=data['author'].strip(),
            description=data.get('description', '').strip(),
            price=validated['price'],
            stock=validated['stock'],
            category_id=validated['category_id'],
            image_url=data['image_url'].strip()
        )
       
        db.session.add(new_book)
        db.session.commit()
       
        return jsonify({
            "message": "Book added successfully",
            "book": new_book.to_dict()
        }), 201


    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding book: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": "Failed to process book creation"
        }), 500


@app.route('/books/<int:book_id>', methods=['PATCH'])
@jwt_required()
def edit_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
   
    data = request.get_json()


    book.title = data.get('title', book.title)
    book.author = data.get('author', book.author)
    book.description = data.get('description', book.description)
    book.price = data.get('price', book.price)
    book.stock = data.get('stock', book.stock)
    book.category_id = data.get('category_id', book.category_id)
    book.image_url = data.get('image_url', book.image_url)


    db.session.commit()
   
    return jsonify(book.to_dict()), 200


@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get(book_id)
    print(id)
   
    if not book:
        return jsonify({"error": "Book not found"}), 404


    OrderItem.query.filter_by(book_id=book_id).delete()
   
    db.session.delete(book)
    db.session.commit()


    return jsonify({"message": "Book deleted successfully"}), 200


@app.route('/wishlist/<int:book_id>', methods=['POST'])
@jwt_required()
def add_to_wishlist(book_id):
    user_id = get_jwt_identity()


    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404


    existing_item = Wishlist.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing_item:
        return jsonify({'message': 'Book already in Wishlist'}), 200


    wishlist_item = Wishlist(user_id=user_id, book_id=book_id)
    db.session.add(wishlist_item)
    db.session.commit()


    return jsonify({'message': 'Book added to Wishlist'}), 201


@app.route('/wishlist', methods=['GET'])
@jwt_required()
def get_wishlist():
    current_user = get_jwt_identity()  
    wishlist_items = Wishlist.query.filter_by(user_id=current_user).all()
    print("Fetched Wishlist:", wishlist_items)  
    return jsonify([item.to_dict() for item in wishlist_items]), 200


@app.route('/wishlist/<int:id>', methods=['GET'])
@jwt_required()
def get_wishlist_by_id(id):
    wishlist_item = Wishlist.query.get(id)
    if wishlist_item:
        return jsonify(wishlist_item.to_dict()), 200
    return jsonify({'error': 'Wishlist item not found'}), 404


@app.route('/wishlist/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_wishlist_item(id):
    user_id = get_jwt_identity()
    wishlist_item = Wishlist.query.filter_by(id=id, user_id=user_id).first()
    if not wishlist_item:
        return jsonify({'error': 'Item not found or unauthorized'}), 404
   
    db.session.delete(wishlist_item)
    db.session.commit()
    return jsonify({'message': 'Item removed'}), 200


@app.route('/cart/<int:book_id>', methods=['POST'])
@jwt_required()
def add_to_cart(book_id):
        user_id = get_jwt_identity()


        book = Book.query.get(book_id)
        if not book:
            return jsonify({'error': 'Book not found'}), 404

        quantity = request.json.get('quantity', 1)  


        existing_item = CartItem.query.filter_by(user_id=user_id, book_id=book_id).first()
        if existing_item:
            return jsonify({'message': 'Book already in your cart'}), 200


        cart_item = CartItem(user_id=user_id, book_id=book_id, quantity=quantity)


        db.session.add(cart_item)
        db.session.commit()


        return jsonify({'message': 'Book added to cart'}), 201


@app.route('/cart/<int:user_id>', methods=['GET'])
@jwt_required()
def get_cart(user_id):
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    return jsonify([item.to_dict() for item in cart_items]), 200




@app.route('/cart/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_cart_item(item_id):
    cart_item = CartItem.query.get(item_id)


    if not cart_item:
        return jsonify({'error': 'Cart item not found'}), 404


    db.session.delete(cart_item)
    db.session.commit()


    return jsonify({'message': 'Cart item deleted successfully'}), 200


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

@app.route('/categories', methods=['POST'])
@jwt_required()
def add_category():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Category name is required'}), 400


    existing_category = Category.query.filter_by(name=name).first()
    if existing_category:
        return jsonify({'error': 'Category already exists'}), 409


    new_category = Category(name=name)
    db.session.add(new_category)
    db.session.commit()


    return jsonify({'message': 'Category added successfully'}), 201

@app.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    categories = Category.query.all()
    return jsonify([category.to_dict() for category in categories]), 200


@app.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    print("Fetching all orders...")  
    orders = Order.query.order_by(Order.datetime.desc()).all()
    print("Orders fetched from DB:", orders)  


    if not orders:
        print("No orders found in the database.")  


    return jsonify([order.to_dict() for order in orders]), 200


@app.route('/orders/<int:id>/', methods=['GET'])
@jwt_required()
def get_orders_by_id(id):
    order_list = Order.query.get(id)
    if order_list:
        return jsonify(order_list.to_dict()), 200
    return jsonify({'error': 'Order not found'}), 404


@app.route('/orders/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_orders(id):
    order = Order.query.get(id)


    if not order:
        return jsonify({'error': 'Order not found'}), 404

    db.session.delete(order)
    db.session.commit()

    return jsonify({'message': 'Order deleted successfully'})
   

@app.route('/orders', methods=['POST'])
@jwt_required()
def place_order():
    user_id = get_jwt_identity()
    data = request.get_json()

    new_order = Order(
        user_id=user_id,
        status='Pending',
        total_price=data['total_price'],
        datetime=datetime.now()
    )
    db.session.add(new_order)
    db.session.commit()

    items = data.get('items', [])
    if not items:
        return jsonify({'error': 'No items provided'}), 400


    for item in items:
        if 'book_id' not in item or 'quantity' not in item or 'price' not in item:
            return jsonify({'error': 'Invalid item data'}), 400


    for item in items:
        order_item = OrderItem(
            order_id=new_order.id,
            book_id=item['book_id'],
            quantity=item['quantity'],
            price=item['price']
        )
        db.session.add(order_item)


    db.session.commit()
    return jsonify({'message': 'Order placed successfully'}), 201

@app.route('/orders/<int:order_id>', methods=['PATCH'])
@jwt_required()
def update_order(order_id):
    try:
        current_user = get_jwt_identity()
        print(f"User {current_user} is updating order {order_id}")

        order = Order.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404

        data = request.get_json()
        new_status = data.get("status")

        if not new_status:
            return jsonify({"error": "Missing status field"}), 400

        old_status = order.status
        order.status = new_status
        db.session.commit()

        if old_status != new_status:
            send_order_update_email(order.user.email, order_id, new_status)

        return jsonify({"message": "Order status updated", "order": {"id": order.id, "status": order.status}}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def send_order_update_email(email, order_id, new_status):
    try:
        message = Mail(
            from_email=SENDGRID_SENDER_EMAIL,
            to_emails=email,
            subject=f"Order {order_id} Update",
            html_content=f"Your order status has been updated to: {new_status}"
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent to {email}, status: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")
    

@app.route('/payments', methods=['POST'])
@jwt_required()
def make_payment():
    data = request.get_json()
    order_id = data.get('order_id')
    payment_method = data.get('payment_method')
    transaction_id = data.get('transaction_id')

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
    
@app.route('/payments', methods=['GET'])
@jwt_required()
def get_payments():
    payment_list = Payment.query.order_by(Payment.created_at.desc()).all()  
    if payment_list:
        return jsonify([payment.to_dict() for payment in payment_list]), 200
    return jsonify({'error': 'No payments found'}), 404


@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    new_access_token = create_access_token(identity=identity, expires_delta=False)
    return jsonify({'access_token': new_access_token}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5555)


