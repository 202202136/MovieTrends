from repositories.movie_repository import MovieRepository
from models.movie import Movie


def get_movie_details(movie_id):
    data = MovieRepository.fetch_movie_by_id(movie_id)
    if data:
        # Map TMDb response fields to the Movie model constructor
        movie = Movie(
            movie_id=data.get('id'),
            title=data.get('title') or data.get('name'),
            overview=data.get('overview') or data.get('overview'),
            poster_path=data.get('poster_path'),
            rating=data.get('vote_average') or data.get('rating'),
            release_date=data.get('release_date') or data.get('first_air_date'),
        )
        return movie
    return None

def get_movie_trailer(movie_id):
    return MovieRepository.fetch_movie_trailer(movie_id)