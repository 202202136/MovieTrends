from data.db import get_connection

def get_user_rating(user_id, tmdb_id, media_type):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT rating_value
        FROM ratings
        WHERE user_id = ? AND tmdb_id = ? AND media_type = ?
    """, (user_id, tmdb_id, media_type))

    row = cursor.fetchone()
    connection.close()

    if row:
        return float(row["rating_value"])
    return None


def upsert_rating(user_id, tmdb_id, media_type, rating_value):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE ratings
        SET rating_value = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ? AND tmdb_id = ? AND media_type = ?
    """, (rating_value, user_id, tmdb_id, media_type))

    if cursor.rowcount == 0:
        cursor.execute("""
            INSERT INTO ratings(user_id, tmdb_id, media_type, rating_value)
            VALUES (?, ?, ?, ?)
        """, (user_id, tmdb_id, media_type, rating_value))

    connection.commit()
    connection.close()


def get_rating_summary(tmdb_id, media_type):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT AVG(rating_value) AS avg_rating, COUNT(*) AS count
        FROM ratings
        WHERE tmdb_id = ? AND media_type = ?
    """, (tmdb_id, media_type))

    row = cursor.fetchone()
    connection.close()

    if not row:
        return 0.0, 0

    avg_rating = float(row["avg_rating"]) if row["avg_rating"] is not None else 0.0
    count = int(row["count"]) if row["count"] is not None else 0
    return avg_rating, count
