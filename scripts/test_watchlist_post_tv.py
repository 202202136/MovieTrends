import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from repositories.movie_repository import MovieRepository
import json

app = create_app()

def run_test():
    client = app.test_client()
    user_id = 1
    tv_id = 77777777
    data = {
        'user_id': str(user_id),
        'movie_id': str(tv_id),
        'media_type': 'tv',
        'title': 'Test Show Y',
        'poster_path': '/test_tv.jpg',
        'vote_average': '9.0',
        'release_date': ''
    }
    resp = client.post('/add_to_watchlist', data=data)
    print('Status:', resp.status_code)
    print('JSON:', resp.get_json())
    user = MovieRepository.get_user_by_id(user_id)
    print('Stored watchlist:', json.dumps(user.get('watchlist', []), indent=2))

if __name__ == '__main__':
    run_test()
