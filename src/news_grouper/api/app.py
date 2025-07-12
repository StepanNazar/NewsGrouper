from apiflask import APIFlask

from news_grouper.api.routes import bp


def create_app() -> APIFlask:
    app = APIFlask(__name__)
    app.register_blueprint(bp)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
