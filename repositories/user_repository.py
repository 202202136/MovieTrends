import sqlite3
import os
from models.user import User

class UserRepository:
    def __init__(self, db_path="data/users.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database and create users table if it doesn't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL
                )
            ''')
            conn.commit()

    def getByEmail(self, email):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT email, password_hash FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            if row:
                return User(row[0], row[1])
        return None

    def add(self, user):
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)',
                           (user.email, user.passwordHash))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Email already exists
                return False