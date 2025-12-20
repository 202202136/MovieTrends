
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from services.movie_service import get_movie_details, get_movie_trailer, get_tv_show_trailer, get_tv_show_details
from repositories.movie_repository import (
    MovieRepository,
    get_trending_movies,
    search_movies,
    get_movie_category,
    get_user_by_id,
)
from datetime import datetime
from repositories.rating_repository import get_user_rating, upsert_rating, get_rating_summary


movie_bp = Blueprint("movie_bp", __name__)

# Fix: server-side sorting; annotate `user` and `in_watchlist`; added JSON
# add/remove watchlist endpoints that accept fallback metadata when TMDb is
# unavailable so watchlist persists per-user.

@movie_bp.route("/movies")
def movies():
    # parse and sanitize query params (single pass)
    raw_category = request.args.get('category', '')
    category = raw_category.strip() if isinstance(raw_category, str) and raw_category.strip() != '' else None

    try:
        page = int(request.args.get('page', 1))
    except (TypeError, ValueError):
        page = 1
    if page < 1:
        page = 1

    # Sorting parameters: sort by rating | release_date | popularity
    sort = request.args.get('sort', '').strip() or None
    order = request.args.get('order', 'desc')

    # Fetch movies for the given category and page
    results, total_pages = get_movie_category(category, page)
    try:
        total_pages = int(total_pages) if total_pages is not None else 1
    except (TypeError, ValueError):
        total_pages = 1

    # Apply optional sorting server-side for flexibility and compatibility
    def _get_field(item, keys):
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

    if sort and results:
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
                pass

    # include current user (if any) so templates can access `user.id`
    user = None
    try:
        user_id = session.get('user_id', 1)
        user = get_user_by_id(user_id)
    except Exception:
        user = None
    # build a set of watchlist ids for quick lookup
    watchlist_ids = set()
    if user and isinstance(user.get('watchlist'), list):
        for item in user.get('watchlist'):
            try:
                if isinstance(item, dict):
                    watchlist_ids.add(int(item.get('id')))
                else:
                    watchlist_ids.add(int(item))
            except Exception:
                continue

    # annotate results with in_watchlist flag so templates render correct button state
    if results:
        for m in results:
            mid = None
            try:
                mid = getattr(m, 'id', None)
            except Exception:
                mid = None
            if mid is None and isinstance(m, dict):
                mid = m.get('id') or m.get('movie_id')
            try:
                in_list = int(mid) in watchlist_ids if mid is not None else False
            except Exception:
                in_list = False
            if isinstance(m, dict):
                m['in_watchlist'] = in_list
            else:
                try:
                    setattr(m, 'in_watchlist', in_list)
                except Exception:
                    pass

    return render_template(
        "movies.html",
        movies=results,
        category=category or '',
        current_page=page,
        total_pages=total_pages,
        sort=sort or '',
        order=order,
        user=user,
    )

@movie_bp.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    movie = get_movie_details(movie_id)
    trailer_key = get_movie_trailer(movie_id)
    user_id = session.get("user_id", 1)
    my_rating = get_user_rating(user_id, movie_id, "movie")
    avg_rating, ratings_count = get_rating_summary(movie_id, "movie")
    user = get_user_by_id(user_id)
    # determine if this movie is in the user's watchlist
    in_watchlist = False
    try:
        if user and isinstance(user.get('watchlist'), list):
            for item in user.get('watchlist'):
                if isinstance(item, dict) and item.get('id') == movie_id:
                    in_watchlist = True
                    break
                try:
                    if int(item) == movie_id:
                        in_watchlist = True
                        break
                except Exception:
                    continue
    except Exception:
        in_watchlist = False

    return render_template(
        "movie_details.html",
        movie=movie,
        trailer_key=trailer_key,
        my_rating=my_rating,
        avg_rating=avg_rating,
        ratings_count=ratings_count,
        user=user,
        in_watchlist=in_watchlist,
    )

@movie_bp.route("/tv/<int:tv_show_id>")
def tv_show_details(tv_show_id):
    tv_show = get_tv_show_details(tv_show_id)
    trailer_key = get_tv_show_trailer(tv_show_id)
    user_id = session.get('user_id', 1)
    my_rating = get_user_rating(user_id, tv_show_id, "tv")
    avg_rating, ratings_count = get_rating_summary(tv_show_id, "tv")
    user = get_user_by_id(user_id)
    # check watchlist membership for tv show
    in_watchlist = False
    try:
        if user and isinstance(user.get('watchlist'), list):
            for item in user.get('watchlist'):
                if isinstance(item, dict) and item.get('id') == tv_show_id:
                    in_watchlist = True
                    break
                try:
                    if int(item) == tv_show_id:
                        in_watchlist = True
                        break
                except Exception:
                    continue
    except Exception:
        in_watchlist = False

    return render_template(
        "movie_details.html",
        movie=tv_show,
        trailer_key=trailer_key,
        my_rating=my_rating,
        avg_rating=avg_rating,
        ratings_count=ratings_count,
        user=user,
        in_watchlist=in_watchlist,
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
    media_type_raw = request.form.get('media_type')
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
    # fetch movie data via repository (try movie endpoint then tv endpoint if media_type suggests)
    movie_data = None
    media_type = (media_type_raw or '').lower() if media_type_raw else None
    if media_type == 'tv':
        movie_data = MovieRepository.fetch_tv_by_id(movie_id)
    else:
        movie_data = MovieRepository.fetch_movie_by_id(movie_id)
        # fallback: if movie fetch fails and media_type is unspecified, try tv
        if not movie_data and not media_type:
            movie_data = MovieRepository.fetch_tv_by_id(movie_id)

    # If TMDb fetch failed, try to pull a saved Movie record or build from provided form metadata
    if not movie_data:
        # try local Movie table
        movie_data = MovieRepository.get_movie_by_tmdb_id(movie_id)
    if not movie_data:
        # attempt to construct from submitted form fields (title/poster_path/vote_average/release_date)
        title = request.form.get('title') or request.form.get('name')
        poster = request.form.get('poster_path')
        vote = request.form.get('vote_average')
        release = request.form.get('release_date')
        if title or poster or vote or release:
            movie_data = {
                'id': movie_id,
                'title': title,
                'poster_path': poster,
                'vote_average': float(vote) if vote else None,
                'release_date': release,
                'media_type': media_type or request.form.get('media_type')
            }

    if not user:
        return jsonify({"error": "User not found"}), 400
    if not movie_data:
        return jsonify({"error": "Movie data not found and no metadata provided"}), 400

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
            'title': movie_data.get('title') or movie_data.get('name'),
            'poster_path': movie_data.get('poster_path'),
            'vote_average': movie_data.get('vote_average'),
            'release_date': movie_data.get('release_date') or movie_data.get('first_air_date'),
            'media_type': movie_data.get('media_type') or ('tv' if movie_data.get('first_air_date') else 'movie')
        })
        # persist
        ok = MovieRepository.save_user_watchlist(user)
        if not ok:
            return jsonify({'error': 'Failed to save watchlist'}), 500

    return jsonify({'success': True, 'message': 'Added to watchlist'})


@movie_bp.route('/remove_from_watchlist', methods=['POST'])
def remove_from_watchlist():
    user_id_raw = request.form.get('user_id')
    movie_id_raw = request.form.get('movie_id')
    if not user_id_raw or not movie_id_raw:
        return jsonify({'error': 'Missing user_id or movie_id'}), 400

    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        user_id = user_id_raw
    try:
        movie_id = int(movie_id_raw)
    except (TypeError, ValueError):
        movie_id = movie_id_raw

    user = get_user_by_id(user_id)
    if not user or 'watchlist' not in user:
        return jsonify({'error': 'User or watchlist not found'}), 400

    original_len = len(user.get('watchlist') or [])
    user['watchlist'] = [item for item in user.get('watchlist', []) if not ((isinstance(item, dict) and item.get('id') == movie_id) or (item == movie_id))]
    if len(user['watchlist']) != original_len:
        ok = MovieRepository.save_user_watchlist(user)
        if not ok:
            return jsonify({'error': 'Failed to save watchlist'}), 500

    return jsonify({'success': True, 'message': 'Removed from watchlist'})


@movie_bp.route('/watchlist')
def watchlist():
    user_id = session.get('user_id', 1)
    user = get_user_by_id(user_id)
    watchlist = []
    if user and isinstance(user.get('watchlist'), list):
        watchlist = user.get('watchlist')
    # enrich watchlist items with poster and other metadata when missing
    for item in watchlist:
        try:
            mid = item.get('id') if isinstance(item, dict) else item
            if isinstance(item, dict):
                if not item.get('poster_path'):
                    data = MovieRepository.fetch_movie_by_id(mid)
                    if data:
                        item.setdefault('poster_path', data.get('poster_path'))
                        item.setdefault('vote_average', data.get('vote_average'))
                        item.setdefault('release_date', data.get('release_date') or data.get('first_air_date'))
                        item.setdefault('media_type', data.get('media_type') or ('tv' if data.get('first_air_date') else 'movie'))
                        item.setdefault('title', data.get('title') or data.get('name'))
        except Exception:
            continue

    return render_template('Watchlist.html', watchlist=watchlist, user=user)
