import sqlite3

# Fix: switched DB to centralized data/database.db and create normalized tables
DB_PATH = "data/database.db"

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        tmdb_id INTEGER NOT NULL,
        media_type TEXT NOT NULL,
        rating_value REAL NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, tmdb_id, media_type)
    );
    """)

    # Users table to store user accounts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        UserID INTEGER PRIMARY KEY AUTOINCREMENT,
        Email TEXT UNIQUE,
        PasswordHash TEXT,
        Username TEXT,
        CreatedAt TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Categories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Category (
        CategoryID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT UNIQUE
    );
    """)

    # Movies table (normalized)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Movie (
        MovieID INTEGER PRIMARY KEY,
        Title TEXT,
        Overview TEXT,
        Rating REAL,
        ReleaseDate TEXT,
        Category INTEGER,
        PosterPath TEXT,
        TrailerURL TEXT,
        FOREIGN KEY(Category) REFERENCES Category(CategoryID)
    );
    """)

    # WatchlistItem linking users to movies
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS WatchlistItem (
        WatchlistItemID INTEGER PRIMARY KEY AUTOINCREMENT,
        UserID INTEGER NOT NULL,
        MovieID INTEGER NOT NULL,
        DateAdded TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(UserID, MovieID),
        FOREIGN KEY(UserID) REFERENCES users(UserID) ON DELETE CASCADE,
        FOREIGN KEY(MovieID) REFERENCES Movie(MovieID) ON DELETE CASCADE
    );
    """)

    # Ensure there is a default guest user with UserID=1
    try:
        cursor.execute("INSERT OR IGNORE INTO users(UserID, Username, Email) VALUES (1, 'guest', 'guest@example.com')")
    except Exception:
        pass

    connection.commit()
    connection.close()
