from flask import Blueprint, render_template
from repositories.movie_repository import MovieRepository

home_blueprint = Blueprint("home", __name__)


@home_blueprint.route("/")
def home():
    movies = MovieRepository.get_trending_movies()
    return render_template("home.html", movies=movies)
