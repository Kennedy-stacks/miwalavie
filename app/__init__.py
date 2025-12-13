from flask import Flask
from dotenv import load_dotenv

from .config import Config
from .extensions import db, login_manager
from .models import User


def create_app() -> Flask:
    load_dotenv()

    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(Config())

    db.init_app(app)
    login_manager.init_app(app)

    from .auth_routes import bp as auth_bp
    from .store_routes import bp as store_bp
    from .admin_routes import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(store_bp)
    app.register_blueprint(admin_bp)

    # Simple CLI to create tables
    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        with app.app_context():
            db.create_all()
        print("Database initialized (tables created).")

    @app.cli.command("create-admin")
    def create_admin():
        """Create an admin user."""
        email = input("Admin email: ").strip().lower()
        password = input("Admin password: ")
        if not email or not password:
            print("Email and password required.")
            return
        existing = User.query.filter_by(email=email).first()
        if existing:
            print("User already exists.")
            return
        user = User(email=email, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print("Admin user created.")

    return app
