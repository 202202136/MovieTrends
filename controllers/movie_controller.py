from flask import Blueprint, render_template, request
from services.movie_service import  get_movie_details, get_movie_trailer

movie_bp = Blueprint("movie_bp", __name__)

@movie_bp.route("/")
def home():
    return render_template("home.html")

@movie_bp.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    movie = get_movie_details(movie_id)
    trailer_key = get_movie_trailer(movie_id)
    return render_template("movie_details.html", movie=movie, trailer_key=trailer_key)

@movie_bp.route("/search")
def search():
    movie_id = request.args.get("id")
    if not movie_id:
        return "No ID provided", 400
    return movie_details(int(movie_id))