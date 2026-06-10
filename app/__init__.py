from flask import Flask
from config import Config
from app.extensions import db, login_manager, migrate
from app.utils import format_uzbekistan_time
import os


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config['UPLOAD_FOLDER_VIDEOS'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_THUMBNAILS'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER_ATTACHMENTS'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
    migrate.init_app(app, db)

    # Register Jinja template filters
    app.add_template_filter(format_uzbekistan_time, 'uz_time')

    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.admin.routes import admin_bp
    from app.ai.routes import ai_bp
    from app.mentor import mentor_bp
    from app.parent import parent_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(ai_bp)
    app.register_blueprint(mentor_bp, url_prefix='/mentor')
    app.register_blueprint(parent_bp, url_prefix='/parent')

    return app
