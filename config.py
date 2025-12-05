import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Use ONLY the API Key (v3 auth) here
    TMDB_API_KEY = os.getenv('TMDB_API_KEY', '')
    
    # API endpoints
    TMDB_BASE_URL = 'https://api.themoviedb.org/3'
    
    # DO NOT add access token here unless you're doing OAuth
    
    # Validate API key exists
    @classmethod
    def validate(cls):
        if not cls.TMDB_API_KEY or cls.TMDB_API_KEY == '':
            raise ValueError("TMDB_API_KEY is not set in .env file!")