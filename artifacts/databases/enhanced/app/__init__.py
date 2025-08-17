from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    db.init_app(app)

    from app.routes.main_routes import main_bp
    from app.routes.rma_routes import rma_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(rma_bp, url_prefix="/rma")

    return app
