class Movie:
    def __init__(self, movie_id, title, overview, poster_path, rating, release_date):
        self.id = movie_id
        self.title = title
        self.overview = overview
        self.poster_path = poster_path
        self.rating = rating
        self.release_date = release_date

    def get_poster_url(self):
        if self.poster_path:
            return "https://image.tmdb.org/t/p/w500" + self.poster_path
        else:
            return None
