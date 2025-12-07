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
            # TMDb returns different keys for movies vs tv shows (title vs name, release_date vs first_air_date)
            movie = Movie(
                movie_id=movie_dict.get("id"),
                title=movie_dict.get("title") or movie_dict.get("name"),
                overview=movie_dict.get("overview") or movie_dict.get("description"),
                poster_path=movie_dict.get("poster_path"),
                rating=movie_dict.get("vote_average"),
                release_date=movie_dict.get("release_date") or movie_dict.get("first_air_date"),
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


def get_trending_movies():
    """Compatibility function used across the codebase.

    Calls `MovieRepository.get_trending_movies()` and keeps previous module-level API.
    """
    return MovieRepository.get_trending_movies()


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
