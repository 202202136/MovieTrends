import os
import sys
import sqlite3
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from data.db import get_connection

@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        yield client

def test_watchlist_and_rating_flow(client):
    test_user_id = 6000
    test_email = 'pytest_user@example.com'
    movie_id = 888888888

    conn = get_connection()
    cur = conn.cursor()
    # ensure test user exists
    cur.execute("INSERT OR IGNORE INTO users(UserID, Username, Email) VALUES (?, ?, ?)", (test_user_id, 'pytest_user', test_email))
    conn.commit()

    # set session user_id
    with client.session_transaction() as sess:
        sess['user_id'] = test_user_id
        sess['user'] = test_email

    # POST add_to_watchlist with fallback metadata
    resp = client.post('/add_to_watchlist', data={
        'user_id': str(test_user_id),
        'movie_id': str(movie_id),
        'media_type': 'movie',
        'title': 'PyTest Movie',
        'poster_path': '/x.jpg',
        'vote_average': '6.6',
        'release_date': '2020-01-01'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data and data.get('success') is True

    # verify DB entries
    cur.execute('SELECT WatchlistItemID FROM WatchlistItem WHERE UserID=? AND MovieID=?', (test_user_id, movie_id))
    wl = cur.fetchone()
    assert wl is not None

    cur.execute('SELECT MovieID, Title FROM Movie WHERE MovieID=?', (movie_id,))
    mv = cur.fetchone()
    assert mv is not None

    # POST rate without following redirect (upsert happens before redirect)
    r = client.post(f'/rate/movie/{movie_id}', data={'rating':'7.5'})
    assert r.status_code in (302, 303, 200)

    cur.execute('SELECT user_id, tmdb_id, rating_value FROM ratings WHERE user_id=? AND tmdb_id=?', (test_user_id, movie_id))
    rating_row = cur.fetchone()
    assert rating_row is not None

    # cleanup test data
    cur.execute('DELETE FROM WatchlistItem WHERE UserID=? AND MovieID=?', (test_user_id, movie_id))
    cur.execute('DELETE FROM Movie WHERE MovieID=?', (movie_id,))
    cur.execute('DELETE FROM ratings WHERE user_id=? AND tmdb_id=?', (test_user_id, movie_id))
    cur.execute('DELETE FROM users WHERE UserID=?', (test_user_id,))
    conn.commit()
    conn.close()
