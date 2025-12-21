import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from repositories.movie_repository import MovieRepository
import json

app = create_app()

def run_test():
    client = app.test_client()
    # ensure test user exists
    user_id = 1
    # choose a fake tmdb id that won't hit external API (we'll provide metadata fallback)
    movie_id = 99999999
    data = {
        'user_id': str(user_id),
        'movie_id': str(movie_id),
        'media_type': 'movie',
        'title': 'Test Movie X',
        'poster_path': '/test.jpg',
        'vote_average': '8.5',
        'release_date': '2020-01-01'
    }
    resp = client.post('/add_to_watchlist', data=data)
    print('Status:', resp.status_code)
    try:
        print('JSON:', resp.get_json())
    except Exception:
        print('Response text:', resp.data.decode())

    # fetch user from repository
    user = MovieRepository.get_user_by_id(user_id)
    print('Stored watchlist:', json.dumps(user.get('watchlist', []), indent=2))

if __name__ == '__main__':
    run_test()
