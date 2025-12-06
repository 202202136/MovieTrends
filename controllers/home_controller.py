from flask import Blueprint, render_template
from repositories.movie_repository import get_trending_movies

home_blueprint = Blueprint("home", __name__)


@home_blueprint.route("/")
def home():
    movies = get_trending_movies()
    return render_template("home.html", movies=movies)
