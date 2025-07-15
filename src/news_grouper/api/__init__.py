from apiflask import APIFlask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from news_grouper.api.config import Config

jwt = JWTManager()
db = SQLAlchemy()
migrate = Migrate()

authorizations = {
    "jwt_access_token": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
    "jwt_refresh_token": {
        "type": "apiKey",
        "in": "cookie",
        "name": "refresh_token_cookie",
    },
    "csrf_refresh_token": {
        "type": "apiKey",
        "in": "header",
        "name": "X-CSRF-TOKEN",
    },
}


def register_blueprints(app: APIFlask) -> None:
    from news_grouper.api.auth.routes import auth
    from news_grouper.api.main.routes import main
    from news_grouper.api.news_grouping.routes import grouping
    from news_grouper.api.news_sources.routes import sources
    from news_grouper.api.profiles.routes import profiles

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(sources)
    app.register_blueprint(grouping)
    app.register_blueprint(profiles)


def register_models() -> None:
    from news_grouper.api.auth import models
    from news_grouper.api.news_sources import models  # noqa
    from news_grouper.api.profiles import models  # noqa


def create_app(config: type[Config]) -> APIFlask:
    app = APIFlask(__name__, title="News Grouper API")
    app.security_schemes = authorizations
    if config:
        app.config.from_object(config)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    register_models()
    register_blueprints(app)
    return app


if __name__ == "__main__":
    from config import DevConfig

    app = create_app(DevConfig)
    app.run(debug=True)
