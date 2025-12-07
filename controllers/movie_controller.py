from flask import Blueprint, render_template, request, jsonify
from services.movie_service import get_movie_details, get_movie_trailer
from repositories.movie_repository import get_trending_movies, search_movies

movie_bp = Blueprint("movie_bp", __name__)

@movie_bp.route("/movies")
def movies():
    movies = get_trending_movies()
    return render_template("movies.html", movies=movies)

@movie_bp.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    movie = get_movie_details(movie_id)
    trailer_key = get_movie_trailer(movie_id)
    return render_template("movie_details.html", movie=movie, trailer_key=trailer_key)

@movie_bp.route("/search")
def search():
    # Simple server-side text search by title using `q` parameter.
    q = request.args.get('q', '').strip()
    if not q:
        # show empty search page when no query provided
        return render_template('search_results.html', movies=[], query='')

    results = search_movies(q)
    return render_template('search_results.html', movies=results, query=q)

@movie_bp.route('/api/movies')
def api_movies():
    category = request.args.get('category')
    page = int(request.args.get('page', 1))
    movies, total_pages = get_trending_movies(category, page)

    return jsonify({
        'movies': movies,
        'page': page,
        'total_pages': total_pages,
        'has_more': page < total_pages
    })