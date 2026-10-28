"""Application setup for the Tour Package website."""
import os
from pathlib import Path

from flask import Flask

from .db import init_db


def create_app(test_config=None):
    """Create the app; optional config lets tests use a separate database."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "local-development-key-change-before-deployment"),
        DATABASE=os.environ.get(
            "TOUR_DATABASE",
            str(Path(app.instance_path) / "tour_package.sqlite3"),
        ),
    )
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_db(app)

    # Register authentication first so g.user is ready for the other routes.
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    from .packages.routes import bp as packages_bp
    app.register_blueprint(packages_bp)

    from .customer.routes import bp as customer_bp
    app.register_blueprint(customer_bp)

    from .admin.routes import bp as admin_bp
    app.register_blueprint(admin_bp)

    return app
