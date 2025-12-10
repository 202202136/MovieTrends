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
            media_type=data.get('media_type') or 'movie',
        )
        return movie
    return None





def get_movie_trailer(movie_id):
    return MovieRepository.fetch_movie_trailer(movie_id)


def get_tv_show_details(tv_id):
    data = MovieRepository.fetch_tv_by_id(tv_id)
    if data:
        movie = Movie(
            movie_id=data.get('id'),
            title=data.get('name') or data.get('title'),
            overview=data.get('overview'),
            poster_path=data.get('poster_path'),
            rating=data.get('vote_average'),
            release_date=data.get('first_air_date') or data.get('release_date'),
            media_type='tv',
        )
        return movie
    return None


def get_tv_show_trailer(tv_id):
    return MovieRepository.fetch_tv_trailer(tv_id)

