import os
import sqlite3
from typing import Optional


DB_DEFAULT_PATH = "club_bot.db"


def get_db_path() -> str:
    """
    Resolve the database path from environment variables.

    Uses DATABASE_PATH from the environment if set, otherwise falls back
    to a sensible default file name in the current working directory.
    """
    return os.getenv("DATABASE_PATH", DB_DEFAULT_PATH)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Create a new SQLite connection.

    The caller is responsible for closing the connection.
    """
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Initialize all database tables if they do not already exist.

    This should be called once on bot startup.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Contributions submitted by members
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                description TEXT NOT NULL,
                links TEXT,
                timestamp TEXT NOT NULL,
                approved INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                reviewed_by INTEGER,
                reviewed_at TEXT
            );
            """
        )

        # Warnings issued by staff
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
            """
        )

        # Generic moderation logs (mute, unmute, warn, clear, etc.)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS moderation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER,
                moderator_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                reason TEXT,
                details TEXT,
                timestamp TEXT NOT NULL
            );
            """
        )

        # Club organizational roles (independent of Discord roles)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS club_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            );
            """
        )

        # Many-to-many relationship: members assigned to club roles
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS member_roles (
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                assigned_at TEXT NOT NULL,
                assigned_by INTEGER NOT NULL,
                PRIMARY KEY (user_id, role_id),
                FOREIGN KEY (role_id) REFERENCES club_roles(id) ON DELETE CASCADE
            );
            """
        )

        conn.commit()
    finally:
        conn.close()


