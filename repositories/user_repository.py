import sqlite3
import os
from models.user import User
from data.db import DB_PATH

# Fix: Use centralized SQLite DB (`data/database.db`) instead of per-file users.db
class UserRepository:
    def __init__(self, db_path=None):
        # Use the centralized database by default
        self.db_path = db_path or DB_PATH
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def getByEmail(self, email):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT Email, PasswordHash FROM users WHERE Email = ?', (email,))
            row = cursor.fetchone()
            if row:
                return User(row[0], row[1])
        return None

    def add(self, user):
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute('INSERT INTO users (Email, PasswordHash) VALUES (?, ?)',
                             (user.email, user.passwordHash))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False