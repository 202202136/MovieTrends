from repositories.movie_repository import MovieRepository
from models.movie_model import Movie
from repositories.movie_repository import MovieRepository

def get_movie_details(movie_id):
    data = MovieRepository.fetch_movie_by_id(movie_id)
    if data:
        return Movie(data)
    return None

def get_movie_trailer(movie_id):
    return MovieRepository.fetch_movie_trailer(movie_id)