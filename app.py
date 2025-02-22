from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_migrate import Migrate
import os

app = Flask(__name__)

# Database configuration moved here
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

api = Api(app)

@app.route("/")
def home():
    return jsonify({"message": "Welcome to the Flask API"})

if __name__ == "__main__":
    app.run(debug=True)
