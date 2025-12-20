from flask import Flask

from controllers.home_controller import home_blueprint
from data.db import init_db
from controllers.movie_controller import movie_bp  #routes in movie_controller are active
from controllers.auth_controller import auth


def create_app():
    app = Flask(
        __name__,
        template_folder="Templates",
        static_folder="static"
    )

    app.secret_key = "csai203-secret"
    app.register_blueprint(home_blueprint)
    app.register_blueprint(movie_bp)  #routes in movie_controller are active
    app.register_blueprint(auth)
    
    return app


    init_db()

    app.register_blueprint(home_blueprint)
    app.register_blueprint(movie_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
