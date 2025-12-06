import os
import requests

from models.movie import Movie

API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"


def get_trending_movies():
    if API_KEY is None:
        print("TMDB_API_KEY is not set.")
        return []

    url = f"{BASE_URL}/trending/movie/week"
    params = {
        "api_key": API_KEY,
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
        movie = Movie(
            movie_id=movie_dict.get("id"),
            title=movie_dict.get("title"),
            overview=movie_dict.get("overview"),
            poster_path=movie_dict.get("poster_path"),
            rating=movie_dict.get("vote_average"),
            release_date=movie_dict.get("release_date"),
        )
        movies.append(movie)

    return movies
