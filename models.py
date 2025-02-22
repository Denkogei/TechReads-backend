from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name}

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    decsription = db.Column(db.String(200), nullable=False)
    price = db.Column(db.integer, nullable=False)
    stock = db.Column(db.integer, nullable=False)
    image_url = db.Column(db.String(500), nullable=False)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "author": self.author}
    
