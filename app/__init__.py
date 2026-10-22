"""Tour Package application factory."""
import os
from pathlib import Path

from flask import Flask

from .db import init_db


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "local-development-key-change-before-deployment"),
        DATABASE=os.environ.get(
            "TOUR_DATABASE",
            str(Path(app.instance_path) / "tour_package.sqlite3"),
        ),
    )
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_db(app)

    # Register the main blueprint first so its before_app_request hook loads g.user.
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    from .admin.routes import bp as admin_bp
    app.register_blueprint(admin_bp)
    return app
