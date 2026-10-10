import io
from flask import Response
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import func
from .models import FoodListing, Claim, User
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from . import db
from .utils import clean_phone
from .models import FoodListing, Claim, User

main = Blueprint("main", __name__)


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def role_required(role):
    if current_user.role != role:
        abort(403)


def expire_old_listings():
    FoodListing.query.filter(
        FoodListing.status == "available",
        FoodListing.expiry_time <= now(),
    ).update({"status": "expired"})
    db.session.commit()

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def process_image(file_storage):
    """Validate, resize and compress an upload. Returns JPEG bytes or None."""
    try:
        img = Image.open(file_storage.stream)
        if img.format not in ALLOWED_FORMATS:
            return None
        img = ImageOps.exif_transpose(img).convert("RGB")   # fix phone rotation
        img.thumbnail((800, 800))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=80, optimize=True)
        return buf.getvalue()
    except (UnidentifiedImageError, OSError):
        return None


def parse_coord(value, limit):
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if -limit <= x <= limit else None


@main.route("/")
@login_required
def listings():
    expire_old_listings()
    items = (
        FoodListing.query
        .filter(FoodListing.status == "available", FoodListing.expiry_time > now())
        .order_by(FoodListing.expiry_time)
        .all()
    )
    return render_template("listings.html", items=items)


@main.route("/add", methods=["GET", "POST"])
@login_required
def add_listing():
    role_required("donor")
    if request.method == "POST":
        try:
            quantity = float(request.form["quantity"])
            expiry = datetime.fromisoformat(request.form["expiry_time"])
        except ValueError:
            flash("Please enter a valid quantity and expiry time.")
            return redirect(url_for("main.add_listing"))

        if quantity <= 0:
            flash("Quantity must be greater than 0.")
            return redirect(url_for("main.add_listing"))

        lat = parse_coord(request.form.get("latitude"), 90)
        lng = parse_coord(request.form.get("longitude"), 180)
        if lat is None or lng is None:
            lat = lng = None

        image_bytes = None
        file = request.files.get("image")
        if file and file.filename:
            image_bytes = process_image(file)
            if image_bytes is None:
                flash("Please upload a valid JPG, PNG or WEBP image.")
                return redirect(url_for("main.add_listing"))

        item = FoodListing(
            donor_id=current_user.id,
            title=request.form["title"].strip(),
            quantity=quantity,
            expiry_time=expiry,
            pickup_address=request.form["pickup_address"].strip(),
            latitude=lat,
            longitude=lng,
            image_data=image_bytes,
            has_image=image_bytes is not None,
        )
        db.session.add(item)
        db.session.commit()
        flash("Food listed successfully!")
        return redirect(url_for("main.my_listings"))
    return render_template("add_listing.html")


@main.route("/my-listings")
@login_required
def my_listings():
    role_required("donor")
    expire_old_listings()
    items = (
        FoodListing.query.filter_by(donor_id=current_user.id)
        .order_by(FoodListing.created_at.desc())
        .all()
    )
    return render_template("my_listings.html", items=items)


@main.route("/claim/<int:listing_id>", methods=["POST"])
@login_required
def claim(listing_id):
    role_required("ngo")
    item = db.session.get(FoodListing, listing_id) or abort(404)

    if item.status != "available" or item.expiry_time <= now():
        flash("Sorry, this food is no longer available.")
        return redirect(url_for("main.listings"))

    item.status = "claimed"
    db.session.add(Claim(listing_id=item.id, ngo_id=current_user.id))
    db.session.commit()
    flash("Claimed! Please collect it before it expires.")
    return redirect(url_for("main.my_claims"))


@main.route("/my-claims")
@login_required
def my_claims():
    role_required("ngo")
    claims = (
        Claim.query.filter_by(ngo_id=current_user.id)
        .order_by(Claim.claimed_at.desc())
        .all()
    )
    return render_template("my_claims.html", claims=claims)


@main.route("/collected/<int:listing_id>", methods=["POST"])
@login_required
def collected(listing_id):
    role_required("ngo")
    item = db.session.get(FoodListing, listing_id) or abort(404)

    if not item.claim or item.claim.ngo_id != current_user.id:
        abort(403)

    item.status = "collected"
    db.session.commit()
    flash("Marked as collected. Thank you!")
    return redirect(url_for("main.my_claims"))


@main.route("/stats")
@login_required
def stats():
    role_required("admin")
    expire_old_listings()

    def total_kg(*statuses):
        return db.session.query(
            func.coalesce(func.sum(FoodListing.quantity), 0)
        ).filter(FoodListing.status.in_(statuses)).scalar()

    return render_template(
        "stats.html",
        donors=User.query.filter_by(role="donor").count(),
        ngos=User.query.filter_by(role="ngo").count(),
        listings=FoodListing.query.count(),
        saved=total_kg("claimed", "collected"),
        collected=total_kg("collected"),
        expired=total_kg("expired"),
    )


@main.route("/image/<int:listing_id>")
@login_required
def food_image(listing_id):
    item = db.session.get(FoodListing, listing_id)
    if not item or not item.has_image:
        abort(404)
    resp = Response(item.image_data, mimetype="image/jpeg")
    resp.headers["Cache-Control"] = "private, max-age=86400"
    return resp


@main.app_errorhandler(413)
def too_large(e):
    flash("Image is too large (max 5 MB).")
    return redirect(url_for("main.add_listing"))

@main.route("/cancel/<int:listing_id>", methods=["POST"])
@login_required
def cancel_listing(listing_id):
    role_required("donor")
    item = db.session.get(FoodListing, listing_id) or abort(404)

    if item.donor_id != current_user.id:
        abort(403)

    if item.status != "available":
        flash("This listing can no longer be cancelled.")
        return redirect(url_for("main.my_listings"))

    item.status = "cancelled"
    db.session.commit()
    flash("Listing cancelled.")
    return redirect(url_for("main.my_listings"))

@main.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        phone = clean_phone(request.form.get("phone"))
        if not phone:
            flash("Please enter a valid phone number (10 to 13 digits).")
            return redirect(url_for("main.profile"))
        current_user.phone = phone
        db.session.commit()
        flash("Phone number saved.")
        return redirect(url_for("main.profile"))
    return render_template("profile.html")