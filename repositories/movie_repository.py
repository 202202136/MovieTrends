import requests

API_Key = "290a6f88c78d596da766ad276b428aa8"
URL = "https://api.themoviedb.org/3"

class MovieRepository:
    @staticmethod
    def fetch_movie_by_id(movie_id):
        url = f"{URL}/movie/{movie_id}?api_key={API_Key}"
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.json()
        return None

    @staticmethod
    def fetch_movie_trailer(movie_id):
        url = f"{URL}/movie/{movie_id}/videos?api_key={API_Key}"
        resp = requests.get(url)
        videos = resp.json().get("results", [])
        trailer = next((v for v in videos if v.get("type")=="Trailer" and v.get("site")=="YouTube"), None)
        return trailer["key"] if trailer else None
