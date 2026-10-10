from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager
from sqlalchemy.orm import deferred


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # donor / ngo / admin
    phone = db.Column(db.String(15))
    listings = db.relationship("FoodListing", backref="donor", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class FoodListing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # in kg
    expiry_time = db.Column(db.DateTime, nullable=False)
    pickup_address = db.Column(db.String(250), nullable=False)

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    has_image = db.Column(db.Boolean, default=False)
    image_data = deferred(db.Column(db.LargeBinary))
    
    status = db.Column(db.String(15), default="available")  # available / claimed / collected / expired
    created_at = db.Column(db.DateTime, default=utcnow)
    claim = db.relationship("Claim", backref="listing", uselist=False)


class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("food_listing.id"), nullable=False)
    ngo_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    claimed_at = db.Column(db.DateTime, default=utcnow)
    ngo = db.relationship("User")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))