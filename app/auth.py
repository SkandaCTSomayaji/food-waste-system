from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from . import db
from .models import User
from .utils import clean_phone

auth = Blueprint("auth", __name__)

ALLOWED_ROLES = {"donor", "ngo"}


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        role = request.form["role"]
        phone = clean_phone(request.form.get("phone"))

        if role not in ALLOWED_ROLES:
            flash("Invalid role selected.")
            return redirect(url_for("auth.register"))

        if not phone:
            flash("Please enter a valid phone number (10 to 13 digits).")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("This email is already registered.")
            return redirect(url_for("auth.register"))

        user = User(name=name, email=email, role=role, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created! Please log in.")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(request.form["password"]):
            login_user(user)
            return redirect(url_for("main.listings"))

        flash("Invalid email or password.")

    return render_template("login.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))