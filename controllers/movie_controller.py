from flask import Blueprint, render_template, request, jsonify
from services.movie_service import get_movie_details, get_movie_trailer, get_tv_show_trailer, get_tv_show_details
from repositories.movie_repository import MovieRepository, get_trending_movies, search_movies, get_movie_category

movie_bp = Blueprint("movie_bp", __name__)

@movie_bp.route("/movies")
def movies():
    # Get category and page parameters from query string
    category = request.args.get('category', '').strip() or None
    page = int(request.args.get('page', 1))
    
    # Fetch movies for the given category and page
    results, total_pages = get_movie_category(category, page)
    
    return render_template("movies.html", 
                         movies=results, 
                         category=category or '',
                         current_page=page,
                         total_pages=total_pages)

@movie_bp.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    movie = get_movie_details(movie_id)
    trailer_key = get_movie_trailer(movie_id)
    return render_template("movie_details.html", movie=movie, trailer_key=trailer_key)

@movie_bp.route("/tv/<int:tv_show_id>")
def tv_show_details(tv_show_id):
    tv_show = get_tv_show_details(tv_show_id)
    trailer_key = get_tv_show_trailer(tv_show_id)
    # reuse movie_details template to display tv show details
    return render_template("movie_details.html", movie=tv_show, trailer_key=trailer_key)

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
    # Normalize empty string -> None so repository treats it as 'all'
    if category == '':
        category = None
    page = int(request.args.get('page', 1))

    # Use repository compatibility wrapper that returns raw TMDb dicts
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
    # ensure media_type present for each result
    for r in results:
        if 'media_type' not in r:
            r['media_type'] = 'tv' if r.get('first_air_date') else 'movie'

    return jsonify({'movies': results, 'page': page, 'has_more': False})