import unittest
from services.movie_service import add_to_watchlist
from repositories.movie_repository import MovieRepository
from models.movie import Movie

class TestMovieService(unittest.TestCase):

    def setUp(self):
        self.user_id = 1
        self.movie = Movie(movie_id=101, title="Test Movie", overview="A test movie", rating=8.5, release_date="2021-12-12")
        self.user = {
            "id": self.user_id,
            "watchlist": []
        }

    def test_add_to_watchlist(self):
        add_to_watchlist(self.user_id, self.movie)
        self.assertIn(self.movie, self.user["watchlist"])

    def test_add_duplicate_movie(self):
        add_to_watchlist(self.user_id, self.movie)
        add_to_watchlist(self.user_id, self.movie)
        self.assertEqual(self.user["watchlist"].count(self.movie), 1)

if __name__ == '__main__':
    unittest.main()
