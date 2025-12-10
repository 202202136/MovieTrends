import os
import requests

from models.movie import Movie

BASE_URL = "https://api.themoviedb.org/3"


class MovieRepository:
    """Repository for communicating with The Movie Database (TMDb) API.

    Uses the `TMDB_API_KEY` environment variable. Provides methods for
    fetching trending movies, fetching a movie by id, and fetching trailers.
    """

    @staticmethod
    def _get_api_key():
        return os.getenv("TMDB_API_KEY")

    @staticmethod
    def get_trending_movies():
        api_key = MovieRepository._get_api_key()
        if not api_key:
            print("TMDB_API_KEY is not set.")
            return []

        # Use the 'all' trending endpoint so results include both movies and TV
        url = f"{BASE_URL}/trending/all/week"
        params = {
            "api_key": api_key,
            "language": "en-US"
        }

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
            # determine media_type if present or infer
            media_type = movie_dict.get('media_type')
            if not media_type:
                # infer from available fields
                media_type = 'tv' if movie_dict.get('first_air_date') else 'movie'

            movie = Movie(
                movie_id=movie_dict.get("id"),
                title=movie_dict.get("title") or movie_dict.get("name"),
                overview=movie_dict.get("overview") or movie_dict.get("description"),
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
            params = {
                "with_genres": "16",
                "page": page
            }
            data = MovieRepository.make_api_request(endpoint, params)
            results = data.get("results", []) if data else []
            # annotate media_type for discover results
            for r in results:
                r.setdefault('media_type', 'movie')
            total_pages = data.get("total_pages", 1) if data else 1
            return results, total_pages
        else:
            endpoint = "/trending/all/day"
        
        params = {"page": page}
        data = MovieRepository.make_api_request(endpoint, params)
        results = data.get("results", []) if data else []
        # ensure media_type present
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


def get_trending_movies(category=None, page=1):
        """Compatibility wrapper:

        - Always returns `(results, total_pages)` tuple for API consistency.
        - If `category` is None/empty, fetches from `/trending/all/day`.
        - Otherwise uses the specific category endpoint.
        """
        return MovieRepository.get_movie_category(category, page)

def get_movie_category(category=None, page=1):
    """Compatibility function used across the codebase.

    Calls `MovieRepository.get_movie_category()` and keeps previous module-level API.
    """
    return MovieRepository.get_movie_category(category, page)


def search_movies(query, page=1):
    """Simple wrapper to search TMDb for movies by title and return raw results.

    Returns a list of result dicts (may be empty).
    """
    api_key = MovieRepository._get_api_key()
    if not api_key:
        print("TMDB_API_KEY is not set.")
        return []

    # Use the multi search endpoint to include movies and TV results
    url = f"{BASE_URL}/search/multi"
    params = {"api_key": api_key, "language": "en-US", "query": query, "page": page, "include_adult": False}
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("results", [])
    except requests.exceptions.RequestException as err:
        print("Error while searching TMDb:", err)
        return []
