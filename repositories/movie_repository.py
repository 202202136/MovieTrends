import os
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from models.movie import Movie
import json
from data.db import get_connection
import traceback

# Fix: migrate watchlist/user persistence to centralized SQLite; add
# save_user_watchlist/save_movie_record with fallback metadata and
# DB-lock-safe upserts. Also added logging for debugging.

BASE_URL = "https://api.themoviedb.org/3"

class MovieRepository:
    @staticmethod
    def _get_api_key():
        return os.getenv("TMDB_API_KEY")

    @staticmethod
    def get_trending_movies():
        api_key = MovieRepository._get_api_key()
        if not api_key:
            print("TMDB_API_KEY is not set.")
            return []
        url = f"{BASE_URL}/trending/all/week"
        params = {"api_key": api_key, "language": "en-US"}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            print("Error while calling TMDb API:", error)
            return []
        data = response.json()
        results = data.get("results", [])
        movies = []
        for movie_dict in results:
            media_type = movie_dict.get('media_type') or ('tv' if movie_dict.get('first_air_date') else 'movie')
            movie = Movie(
                movie_id=movie_dict.get("id"),
                title=movie_dict.get("title") or movie_dict.get("name"),
                overview=movie_dict.get("overview"),
                poster_path=movie_dict.get("poster_path"),
                rating=movie_dict.get("vote_average"),
                release_date=movie_dict.get("release_date") or movie_dict.get("first_air_date"),
                media_type=media_type,
            )
            movies.append(movie)
        return movies

    @staticmethod
    def fetch_movie_by_id(movie_id):
        api_key = MovieRepository._get_api_key()
        if not api_key:
            print("TMDB_API_KEY is not set.")
            return None
        url = f"{BASE_URL}/movie/{movie_id}"
        params = {"api_key": api_key, "language": "en-US"}
        try:
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as err:
            print(f"Error fetching movie {movie_id}:", err)
            return None

    @staticmethod
    def fetch_movie_trailer(movie_id):
        api_key = MovieRepository._get_api_key()
        if not api_key:
            print("TMDB_API_KEY is not set.")
            return None
        url = f"{BASE_URL}/movie/{movie_id}/videos"
        params = {"api_key": api_key}
        try:
            resp = requests.get(url, params=params)
            resp.raise_for_status()
        except requests.exceptions.RequestException as err:
            print(f"Error fetching trailers for {movie_id}:", err)
            return None
        videos = resp.json().get("results", [])
        trailer = next((v for v in videos if v.get("type") == "Trailer" and v.get("site") == "YouTube"), None)
        return trailer.get("key") if trailer else None

    @staticmethod
    def fetch_tv_by_id(tv_id):
        api_key = MovieRepository._get_api_key()
        if not api_key:
            print("TMDB_API_KEY is not set.")
            return None
        url = f"{BASE_URL}/tv/{tv_id}"
        params = {"api_key": api_key, "language": "en-US"}
        try:
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as err:
            print(f"Error fetching tv show {tv_id}:", err)
            return None

    @staticmethod
    def fetch_tv_trailer(tv_id):
        api_key = MovieRepository._get_api_key()
        if not api_key:
            print("TMDB_API_KEY is not set.")
            return None
        url = f"{BASE_URL}/tv/{tv_id}/videos"
        params = {"api_key": api_key}
        try:
            resp = requests.get(url, params=params)
            resp.raise_for_status()
        except requests.exceptions.RequestException as err:
            print(f"Error fetching trailers for tv {tv_id}:", err)
            return None
        videos = resp.json().get("results", [])
        trailer = next((v for v in videos if v.get("type") == "Trailer" and v.get("site") == "YouTube"), None)
        return trailer.get("key") if trailer else None

    @staticmethod
    def get_movie_category(category=None, page=1):
        if category == "Movie":
            endpoint = "/trending/movie/day"
        elif category == "Series":
            endpoint = "/trending/tv/day"
        elif category == "Cartoon":
            endpoint = "/discover/movie"
            params = {"with_genres": "16", "page": page}
            data = MovieRepository.make_api_request(endpoint, params)
            results = data.get("results", []) if data else []
            for r in results:
                r.setdefault('media_type', 'movie')
            total_pages = data.get("total_pages", 1) if data else 1
            return results, total_pages
        else:
            endpoint = "/trending/all/day"
        params = {"page": page}
        data = MovieRepository.make_api_request(endpoint, params)
        results = data.get("results", []) if data else []
        for r in results:
            if 'media_type' not in r:
                r['media_type'] = 'tv' if r.get('first_air_date') else 'movie'
        total_pages = data.get("total_pages", 1) if data else 1
        return results, total_pages

    @staticmethod
    def make_api_request(endpoint, params=None):
        params = params or {}
        api_key = MovieRepository._get_api_key()
        if not api_key:
            print("TMDB_API_KEY is not set.")
            return None
        params['api_key'] = api_key
        url = f"{BASE_URL}{endpoint}"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as err:
            print(f"API request error for {endpoint}:", err)
            return None

    @staticmethod
    def get_user_by_id(user_id):
        # Retrieve user and their watchlist from the SQLite database (normalized schema)
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT UserID, Username, Email FROM users WHERE UserID = ?", (user_id,))
            row = cur.fetchone()
            if not row:
                conn.close()
                return None

            user = {
                'id': row['UserID'],
                'username': row['Username'],
                'email': row['Email'],
            }

            # Load watchlist items joined with Movie table
            cur.execute(
                """
                SELECT m.MovieID, m.Title, m.PosterPath, m.Rating, m.ReleaseDate, c.Name as CategoryName
                FROM WatchlistItem w
                JOIN Movie m ON w.MovieID = m.MovieID
                LEFT JOIN Category c ON m.Category = c.CategoryID
                WHERE w.UserID = ?
                ORDER BY w.DateAdded DESC
                """,
                (user_id,)
            )
            items = []
            for r in cur.fetchall():
                media_type = r['CategoryName'] if r['CategoryName'] else ('tv' if r['ReleaseDate'] is None else 'movie')
                items.append({
                    'id': r['MovieID'],
                    'title': r['Title'],
                    'poster_path': r['PosterPath'],
                    'vote_average': r['Rating'],
                    'release_date': r['ReleaseDate'],
                    'category': r['CategoryName'],
                    'media_type': media_type,
                })

            user['watchlist'] = items
            conn.close()
            return user
        except Exception:
            return None

    @staticmethod
    def save_user_watchlist(user):
        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            user_id = user.get('id')
            if user_id is None:
                if conn:
                    conn.close()
                print('save_user_watchlist: missing user id')
                return False

            print(f"save_user_watchlist: saving watchlist for user {user_id} items={len(user.get('watchlist', []))}")

            # Ensure user exists
            cur.execute("INSERT OR IGNORE INTO users(UserID, Username, Email) VALUES (?, ?, ?)", (user_id, user.get('username'), user.get('email')))

            # Delete previous watchlist items for this user
            cur.execute("DELETE FROM WatchlistItem WHERE UserID = ?", (user_id,))

            for item in user.get('watchlist', []):
                try:
                    tmdb_id = int(item.get('id')) if isinstance(item, dict) else int(item)
                except Exception:
                    continue

                # Ensure movie record exists in Movie table. If not, try to fetch from TMDb and save.
                cur.execute("SELECT MovieID FROM Movie WHERE MovieID = ?", (tmdb_id,))
                if not cur.fetchone():
                    data = None
                    try:
                        data = MovieRepository.fetch_movie_by_id(tmdb_id)
                    except Exception:
                        data = None
                    if not data:
                        try:
                            data = MovieRepository.fetch_tv_by_id(tmdb_id)
                        except Exception:
                            data = None

                    # helper to upsert using the current cursor to avoid separate DB connections
                    def _upsert_with_cursor(cur, movie_data):
                        try:
                            tmdb = movie_data.get('id') or movie_data.get('movie_id')
                            if not tmdb:
                                return
                            title = movie_data.get('title') or movie_data.get('name')
                            overview = movie_data.get('overview')
                            rating = movie_data.get('vote_average') or movie_data.get('rating')
                            release_date = movie_data.get('release_date') or movie_data.get('first_air_date')
                            poster = movie_data.get('poster_path')
                            # Category handling
                            media_type_local = movie_data.get('media_type') or ('tv' if movie_data.get('first_air_date') else 'movie')
                            category_id_local = None
                            if media_type_local:
                                cur.execute("SELECT CategoryID FROM Category WHERE Name = ?", (media_type_local,))
                                row = cur.fetchone()
                                if row:
                                    category_id_local = row['CategoryID']
                                else:
                                    cur.execute("INSERT INTO Category(Name) VALUES (?)", (media_type_local,))
                                    category_id_local = cur.lastrowid
                            cur.execute(
                                "INSERT OR REPLACE INTO Movie(MovieID, Title, Overview, Rating, ReleaseDate, Category, PosterPath, TrailerURL) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (tmdb, title, overview, rating, release_date, category_id_local, poster, None)
                            )
                        except Exception:
                            traceback.print_exc()

                    if data:
                        _upsert_with_cursor(cur, data)
                    else:
                        if isinstance(item, dict):
                            fallback = {
                                'id': tmdb_id,
                                'title': item.get('title') or item.get('name'),
                                'overview': item.get('overview') or '',
                                'vote_average': item.get('vote_average') or item.get('rating'),
                                'release_date': item.get('release_date') or item.get('first_air_date'),
                                'poster_path': item.get('poster_path'),
                                'media_type': item.get('media_type')
                            }
                            _upsert_with_cursor(cur, fallback)

                # Insert watchlist item linking to Movie.MovieID
                cur.execute("INSERT OR IGNORE INTO WatchlistItem(UserID, MovieID) VALUES (?, ?)", (user_id, tmdb_id))

            conn.commit()
            if conn:
                conn.close()
            return True
        except Exception:
            print('save_user_watchlist: exception')
            traceback.print_exc()
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
            return False

    @staticmethod
    def save_movie_record(movie_data):
        """Insert or update a movie record in the Movie table using TMDb data or fallback metadata."""
        try:
            conn = get_connection()
            cur = conn.cursor()
            tmdb_id = movie_data.get('id') or movie_data.get('movie_id')
            if not tmdb_id:
                conn.close()
                return
            title = movie_data.get('title') or movie_data.get('name')
            overview = movie_data.get('overview')
            rating = movie_data.get('vote_average') or movie_data.get('rating')
            release_date = movie_data.get('release_date') or movie_data.get('first_air_date')
            poster = movie_data.get('poster_path')
            # trailer url: try to find youtube trailer key
            trailer_key = None
            try:
                videos = movie_data.get('videos', {}).get('results', []) if isinstance(movie_data, dict) else []
                if videos:
                    trailer = next((v for v in videos if v.get('type') == 'Trailer' and v.get('site') == 'YouTube'), None)
                    trailer_key = f"https://www.youtube.com/watch?v={trailer.get('key')}" if trailer else None
            except Exception:
                trailer_key = None

            # Category: store media_type string in Category table and reference by id
            media_type = movie_data.get('media_type') or ('tv' if movie_data.get('first_air_date') else 'movie')
            category_id = None
            try:
                if media_type:
                    cur.execute("SELECT CategoryID FROM Category WHERE Name = ?", (media_type,))
                    row = cur.fetchone()
                    if row:
                        category_id = row['CategoryID']
                    else:
                        cur.execute("INSERT INTO Category(Name) VALUES (?)", (media_type,))
                        category_id = cur.lastrowid
            except Exception:
                category_id = None

            cur.execute(
                "INSERT OR REPLACE INTO Movie(MovieID, Title, Overview, Rating, ReleaseDate, Category, PosterPath, TrailerURL) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (tmdb_id, title, overview, rating, release_date, category_id, poster, trailer_key)
            )
            conn.commit()
            conn.close()
        except Exception:
            traceback.print_exc()
            return

    @staticmethod
    def get_movie_by_tmdb_id(tmdb_id):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT m.MovieID, m.Title, m.Overview, m.Rating, m.ReleaseDate, m.Category, m.PosterPath, m.TrailerURL, c.Name as MediaType FROM Movie m LEFT JOIN Category c ON m.Category = c.CategoryID WHERE m.MovieID = ?", (tmdb_id,))
            r = cur.fetchone()
            conn.close()
            if not r:
                return None
            return {
                'id': r['MovieID'],
                'title': r['Title'],
                'overview': r['Overview'],
                'rating': r['Rating'],
                'release_date': r['ReleaseDate'],
                'poster_path': r['PosterPath'],
                'trailer_url': r['TrailerURL'],
                'media_type': r['MediaType']
            }
        except Exception:
            return None

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    @staticmethod
    def check_password(stored_hash, password):
        return check_password_hash(stored_hash, password)

def get_trending_movies(category=None, page=1):
    return MovieRepository.get_movie_category(category, page)

def get_movie_category(category=None, page=1):
    return MovieRepository.get_movie_category(category, page)

def get_user_by_id(user_id):
    return MovieRepository.get_user_by_id(user_id)

def search_movies(query, page=1):
    api_key = MovieRepository._get_api_key()
    if not api_key:
        print("TMDB_API_KEY is not set.")
        return []
    url = f"{BASE_URL}/search/multi"
    params = {"api_key": api_key, "language": "en-US", "query": query, "page": page, "include_adult": False}
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("results", [])
    except requests.exceptions.RequestException as err:
        print("Error while searching TMDb:", err)
        return []
def save_user_watchlist(user):
    return MovieRepository.save_user_watchlist(user)