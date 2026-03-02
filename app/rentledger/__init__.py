import click
from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from . import models  # noqa

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    from .routes import bp
    app.register_blueprint(bp)

    from .auth import auth_bp
    app.register_blueprint(auth_bp)

    with app.app_context():
        from flask_migrate import upgrade
        upgrade()
        _seed_admin(app)

    @app.cli.command('create-user')
    @click.argument('username')
    @click.argument('password')
    def create_user(username, password):
        """Create a new user. Usage: flask create-user <username> <password>"""
        from .models import User
        if User.query.filter_by(username=username).first():
            click.echo(f"Error: username '{username}' already exists.")
            return
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"User '{username}' created.")

    return app


def _seed_admin(app):
    username = app.config.get('ADMIN_USERNAME')
    password = app.config.get('ADMIN_PASSWORD')
    if not username or not password:
        return
    from .models import User
    if not User.query.filter_by(username=username).first():
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
