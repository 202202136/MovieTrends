from flask import Flask
from controllers.home_controller import home_blueprint


def create_app():
    app = Flask(
        __name__,
        template_folder="Templates", 
        static_folder="static"
    )

    app.register_blueprint(home_blueprint)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
