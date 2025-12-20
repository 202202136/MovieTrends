import unittest
from app import app
from flask import jsonify

class TestMovieController(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.user_id = 1
        self.movie_id = 101

    def test_add_to_watchlist_route(self):
        response = self.app.post('/add_to_watchlist', data={
            'user_id': self.user_id,
            'movie_id': self.movie_id
        })
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data["success"])

    def test_add_to_watchlist_invalid_user(self):
        response = self.app.post('/add_to_watchlist', data={
            'user_id': 9999,
            'movie_id': self.movie_id
        })
        self.assertEqual(response.status_code, 400)
        json_data = response.get_json()
        self.assertFalse(json_data["success"])

if __name__ == '__main__':
    unittest.main()
