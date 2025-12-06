from flask import Flask, render_template, request, jsonify
import requests
import os
import logging

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['API_KEY'] = os.environ.get('API_KEY', "your_tmdb_api_key")
app.config['BASE_URL'] = "https://api.themoviedb.org/3"
app.config['IMAGE_BASE_URL'] = "https://image.tmdb.org/t/p/w500"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MovieService:
    @staticmethod
    def get_trending_movies(category=None, page=1):
        if category == "Movie":
            endpoint = "/trending/movie/day"
        elif category == "Series":
            endpoint = "/trending/tv/day"
        elif category == "Cartoon":
            endpoint = "/discover/movie"
            params = {
                "with_genres": "16",
                "page": page
            }
            data = MovieService.make_api_request(endpoint, params)
            return data.get("results", []), data.get("total_pages", 1)
        else:
            endpoint = "/trending/all/day"
        
        params = {"page": page}
        data = MovieService.make_api_request(endpoint, params)
        return data.get("results", []), data.get("total_pages", 1)

    @staticmethod
    def make_api_request(endpoint, params=None):
        params = params or {}
        params['api_key'] = app.config['API_KEY']
        url = f"{app.config['BASE_URL']}{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()


@app.route('/')
def home():
    category = request.args.get('category', 'Movie')
    page = int(request.args.get('page', 1))
    movies, total_pages = MovieService.get_trending_movies(category, page)

    return render_template(
        'home.html', 
        movies=movies, 
        current_category=category,
        current_page=page,
        total_pages=total_pages,
        image_base_url=app.config['IMAGE_BASE_URL']
    )


@app.route('/api/movies')
def api_movies():
    category = request.args.get('category')
    page = int(request.args.get('page', 1))
    movies, total_pages = MovieService.get_trending_movies(category, page)

    return jsonify({
        'movies': movies,
        'page': page,
        'total_pages': total_pages,
        'has_more': page < total_pages
    })

if __name__ == '__main__':
    app.run(debug=True)
