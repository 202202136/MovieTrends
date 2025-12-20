from flask import Blueprint, render_template, request, jsonify
from services.movie_service import get_movie_details, get_movie_trailer, get_tv_show_trailer, get_tv_show_details
from repositories.movie_repository import MovieRepository, get_trending_movies, search_movies, get_movie_category
from datetime import datetime

movie_bp = Blueprint("movie_bp", __name__)

@movie_bp.route("/movies")
def movies():
    # Get category and page parameters from query string
    category = request.args.get('category', '').strip() or None
    page = int(request.args.get('page', 1))
    # Sorting parameters: sort by rating | release_date | popularity
    sort = request.args.get('sort', '').strip() or None
    order = request.args.get('order', 'desc')
    
    # Fetch movies for the given category and page
    results, total_pages = get_movie_category(category, page)
    # Apply optional sorting server-side for flexibility and compatibility
    def _get_field(item, keys):
        # support dicts and objects
        for k in keys:
            try:
                val = getattr(item, k)
            except Exception:
                val = None
            if val is None and isinstance(item, dict):
                val = item.get(k)
            if val is not None:
                return val
        return None

    if sort:
        reverse = (order == 'desc')
        if sort == 'rating':
            keyfn = lambda m: float(_get_field(m, ['vote_average', 'rating']) or 0)
        elif sort == 'release_date':
            def keyfn(m):
                s = _get_field(m, ['release_date', 'first_air_date'])
                if not s:
                    return datetime.min
                try:
                    return datetime.strptime(s, '%Y-%m-%d')
                except Exception:
                    return datetime.min
        elif sort == 'popularity':
            keyfn = lambda m: float(_get_field(m, ['popularity']) or 0)
        else:
            keyfn = None

        if keyfn:
            try:
                results = sorted(results, key=keyfn, reverse=reverse)
            except Exception:
                # If sorting fails, leave original order
                pass
    
    return render_template("movies.html", 
                         movies=results, 
                         category=category or '',
                         current_page=page,
                         total_pages=total_pages,
                         sort=sort or '')#added sort to template context

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