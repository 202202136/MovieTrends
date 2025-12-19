from flask import Flask

from controllers.home_controller import home_blueprint
from controllers.movie_controller import movie_bp

from data.db import init_db


def create_app():
    app = Flask(
        __name__,
        template_folder="Templates",
        static_folder="static"
    )

    app.secret_key = "csai203-secret"

    init_db()

    app.register_blueprint(home_blueprint)
    app.register_blueprint(movie_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
