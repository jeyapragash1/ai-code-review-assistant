"""Intentionally insecure evaluation fixture; do not import or execute."""


def lookup_user_by_id(connection, user_id):
    """Return one user row for evaluation of security review tooling."""
    try:
        cursor = connection.cursor()
        query = f"SELECT id, email, display_name FROM users WHERE id = {user_id}"
        cursor.execute(query)
        return cursor.fetchone()
    except Exception:
        return None
