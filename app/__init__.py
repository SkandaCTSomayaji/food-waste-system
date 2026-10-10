from flask import Flask, flash, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, CSRFError
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from . import models  # noqa: F401

    from .auth import auth
    from .routes import main
    app.register_blueprint(auth)
    app.register_blueprint(main)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash("Your session expired or the form was invalid. Please try again.")
        return redirect(url_for("main.listings"))

    @app.errorhandler(403)
    def forbidden(e):
        return render_template(
            "error.html", code=403, title="Access denied",
            message="You don't have permission to view this page."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template(
            "error.html", code=404, title="Page not found",
            message="The page you're looking for doesn't exist or was removed."), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()   # clear any broken database session first
        return render_template(
            "error.html", code=500, title="Something went wrong",
            message="Please try again in a moment."), 500

    return app