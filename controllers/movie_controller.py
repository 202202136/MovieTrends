from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from services.movie_service import get_movie_details, get_movie_trailer, get_tv_show_trailer, get_tv_show_details
from repositories.movie_repository import (
    MovieRepository,
    get_trending_movies,
    search_movies,
    get_movie_category,
    get_user_by_id,
)

movie_bp = Blueprint("movie_bp", __name__)

@movie_bp.route("/movies")
def movies():
    # parse and sanitize query params
    raw_category = request.args.get('category', '')
    category = raw_category.strip() if isinstance(raw_category, str) else ''
    if category == '':
        category = None

    # safe page parsing
    try:
        page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    if page < 1:
        page = 1

    results, total_pages = get_movie_category(category, page)
    try:
        total_pages = int(total_pages) if total_pages is not None else 1
    except (TypeError, ValueError):
        total_pages = 1

    return render_template(
        "movies.html",
        movies=results,
        category=category or '',
        current_page=page,
        total_pages=total_pages,
    )

@movie_bp.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    movie = get_movie_details(movie_id)
    trailer_key = get_movie_trailer(movie_id)
    return render_template("movie_details.html", movie=movie, trailer_key=trailer_key)

@movie_bp.route("/tv/<int:tv_show_id>")
def tv_show_details(tv_show_id):
    tv_show = get_tv_show_details(tv_show_id)
    trailer_key = get_tv_show_trailer(tv_show_id)
    return render_template("movie_details.html", movie=tv_show, trailer_key=trailer_key)

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
    try:
        page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    results, total_pages = get_movie_category(category, page)
    return jsonify({
        'movies': results,
        'page': page,
        'total_pages': total_pages or 1,
        'has_more': (page < (total_pages or 1)) if isinstance(total_pages, int) else False,
    })

@movie_bp.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    try:
        page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    if not q:
        return jsonify({'movies': [], 'page': page, 'has_more': False})
    results = search_movies(q, page)
    for r in results:
        if 'media_type' not in r:
            r['media_type'] = 'tv' if r.get('first_air_date') else 'movie'
    # search endpoint does not currently expose total_pages from repository; return has_more False
    return jsonify({'movies': results, 'page': page, 'has_more': False})

@movie_bp.route('/add_to_watchlist', methods=['POST'])
def add_to_watchlist_route():
    user_id_raw = request.form.get('user_id')
    movie_id_raw = request.form.get('movie_id')
    if not user_id_raw or not movie_id_raw:
        return jsonify({"error": "Missing user_id or movie_id"}), 400

    # try converting to int where appropriate
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        user_id = user_id_raw
    try:
        movie_id = int(movie_id_raw)
    except (TypeError, ValueError):
        movie_id = movie_id_raw

    user = get_user_by_id(user_id)
    # fetch movie data via repository (returns dict or None)
    movie_data = MovieRepository.fetch_movie_by_id(movie_id)

    if not user or not movie_data:
        return jsonify({"error": "User or movie not found"}), 400

    # Ensure watchlist exists and is a list
    if 'watchlist' not in user or not isinstance(user.get('watchlist'), list):
        user['watchlist'] = []

    # Avoid duplicates (compare by id)
    movie_id_val = movie_data.get('id')
    exists = any((isinstance(item, dict) and item.get('id') == movie_id_val) or (item == movie_id_val) for item in user['watchlist'])
    if not exists:
        # keep a lightweight entry in watchlist (id + title)
        user['watchlist'].append({
            'id': movie_id_val,
            'title': movie_data.get('title') or movie_data.get('name')
        })
        # persist
        MovieRepository.save_user_watchlist(user)

    return redirect(url_for('movie_bp.movies'))
