from flask import Blueprint, render_template
from repositories.movie_repository import MovieRepository

home_blueprint = Blueprint("home", __name__)


@home_blueprint.route("/")
def home():
    # Render the designated site Home page
    movies = MovieRepository.get_trending_movies()
    return render_template("Home.html", movies=movies)
