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

def ensure_user(conn, user_id, email='unit_user@example.com'):
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users(UserID, Username, Email) VALUES (?, ?, ?)", (user_id, 'unit_user', email))
    conn.commit()


def test_add_and_remove_watchlist(client):
    test_user_id = 7000
    movie_id = 777777777

    conn = get_connection()
    ensure_user(conn, test_user_id)

    with client.session_transaction() as sess:
        sess['user_id'] = test_user_id
        sess['user'] = 'unit_user@example.com'

    # Add to watchlist
    resp = client.post('/add_to_watchlist', data={
        'user_id': str(test_user_id),
        'movie_id': str(movie_id),
        'media_type': 'movie',
        'title': 'Unit Test Movie',
        'poster_path': '/u.jpg',
        'vote_average': '5.5',
        'release_date': '2021-01-01'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data and data.get('success') is True

    cur = conn.cursor()
    cur.execute('SELECT WatchlistItemID FROM WatchlistItem WHERE UserID=? AND MovieID=?', (test_user_id, movie_id))
    assert cur.fetchone() is not None

    # Remove from watchlist
    resp2 = client.post('/remove_from_watchlist', data={'user_id': str(test_user_id), 'movie_id': str(movie_id)})
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2 and data2.get('success') is True

    cur.execute('SELECT WatchlistItemID FROM WatchlistItem WHERE UserID=? AND MovieID=?', (test_user_id, movie_id))
    assert cur.fetchone() is None

    # cleanup
    cur.execute('DELETE FROM Movie WHERE MovieID=?', (movie_id,))
    cur.execute('DELETE FROM ratings WHERE user_id=? AND tmdb_id=?', (test_user_id, movie_id))
    cur.execute('DELETE FROM users WHERE UserID=?', (test_user_id,))
    conn.commit()
    conn.close()


def test_rate_upsert(client):
    test_user_id = 7001
    movie_id = 777777778

    conn = get_connection()
    ensure_user(conn, test_user_id, email='unit_rate@example.com')

    with client.session_transaction() as sess:
        sess['user_id'] = test_user_id
        sess['user'] = 'unit_rate@example.com'

    resp = client.post(f'/rate/movie/{movie_id}', data={'rating': '8.0'})
    assert resp.status_code in (200, 302, 303)

    cur = conn.cursor()
    cur.execute('SELECT user_id, tmdb_id, rating_value FROM ratings WHERE user_id=? AND tmdb_id=?', (test_user_id, movie_id))
    row = cur.fetchone()
    assert row is not None
    # rating_value may be stored as float or text; coerce
    assert float(row[2]) == pytest.approx(8.0)

    # cleanup
    cur.execute('DELETE FROM ratings WHERE user_id=? AND tmdb_id=?', (test_user_id, movie_id))
    cur.execute('DELETE FROM Movie WHERE MovieID=?', (movie_id,))
    cur.execute('DELETE FROM users WHERE UserID=?', (test_user_id,))
    conn.commit()
    conn.close()


def test_movies_page_loads_sorted(client):
    # Basic smoke test: ensure the movies page responds successfully with sort params
    resp = client.get('/movies?sort=rating&order=desc')
    assert resp.status_code == 200
    assert resp.data and len(resp.data) > 0
