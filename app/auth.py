import hashlib
from dataclasses import dataclass

from app.database import get_connection


@dataclass
class AuthUser:
    id: int
    username: str
    role: str


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def ensure_default_admin() -> None:
    conn = get_connection()
    row = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", hash_password("admin123"), "admin"),
        )
        conn.commit()
    conn.close()


def authenticate(username: str, password: str) -> AuthUser | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT id, username, role, password_hash FROM users WHERE username=?",
        (username,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    if row["password_hash"] != hash_password(password):
        return None
    return AuthUser(id=row["id"], username=row["username"], role=row["role"])
