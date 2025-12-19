from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from services.movie_service import get_movie_details, get_movie_trailer, get_tv_show_trailer, get_tv_show_details
from repositories.movie_repository import MovieRepository, get_trending_movies, search_movies, get_movie_category
from repositories.rating_repository import get_user_rating, upsert_rating, get_rating_summary

movie_bp = Blueprint("movie_bp", __name__)

@movie_bp.route("/movies")
def movies():
    category = request.args.get('category', '').strip() or None
    page = int(request.args.get('page', 1))
    results, total_pages = get_movie_category(category, page)

    return render_template(
        "movies.html",
        movies=results,
        category=category or '',
        current_page=page,
        total_pages=total_pages
    )

@movie_bp.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    movie = get_movie_details(movie_id)
    trailer_key = get_movie_trailer(movie_id)
    user_id = session.get("user_id", 1)
    my_rating = get_user_rating(user_id, movie_id, "movie")
    avg_rating, ratings_count = get_rating_summary(movie_id, "movie")

    return render_template(
        "movie_details.html",
        movie=movie,
        trailer_key=trailer_key,
        my_rating=my_rating,
        avg_rating=avg_rating,
        ratings_count=ratings_count
    )

@movie_bp.route("/tv/<int:tv_show_id>")
def tv_show_details(tv_show_id):
    tv_show = get_tv_show_details(tv_show_id)
    trailer_key = get_tv_show_trailer(tv_show_id)
    user_id = session.get("user_id", 1)
    my_rating = get_user_rating(user_id, tv_show_id, "tv")
    avg_rating, ratings_count = get_rating_summary(tv_show_id, "tv")

    return render_template(
        "movie_details.html",
        movie=tv_show,
        trailer_key=trailer_key,
        my_rating=my_rating,
        avg_rating=avg_rating,
        ratings_count=ratings_count
    )

@movie_bp.route("/rate/<media_type>/<int:tmdb_id>", methods=["POST"])
def save_rating(media_type, tmdb_id):
    if media_type not in ("movie", "tv"):
        return redirect(url_for("home.home"))

    user_id = session.get("user_id", 1)

    try:
        rating_value = float(request.form.get("rating", "0"))
    except ValueError:
        rating_value = 0.0

    if rating_value < 0:
        rating_value = 0.0
    if rating_value > 10:
        rating_value = 10.0

    upsert_rating(user_id, tmdb_id, media_type, rating_value)

    if media_type == "tv":
        return redirect(url_for("movie_bp.tv_show_details", tv_show_id=tmdb_id))
    return redirect(url_for("movie_bp.movie_details", movie_id=tmdb_id))

@movie_bp.route("/search")
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return render_template('search_results.html', movies=[], query='')

    results = search_movies(q)
    return render_template('search_results.html', movies=results, query=q)

@movie_bp.route('/api/movies')
def api_movies():
    category = request.args.get('category')
    if category == '':
        category = None
    page = int(request.args.get('page', 1))

    results, total_pages = get_movie_category(category, page)

    return jsonify({
        'movies': results,
        'page': page,
        'total_pages': total_pages,
        'has_more': page < total_pages
    })

@movie_bp.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    if not q:
        return jsonify({'movies': [], 'page': page, 'has_more': False})

    results = search_movies(q, page)
    for r in results:
        if 'media_type' not in r:
            r['media_type'] = 'tv' if r.get('first_air_date') else 'movie'

    return jsonify({'movies': results, 'page': page, 'has_more': False})
