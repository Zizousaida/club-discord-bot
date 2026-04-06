from __future__ import annotations

import sqlite3

from database import db, queries


def _init_in_memory() -> sqlite3.Connection:
    conn = db.get_connection(":memory:")
    # Create schema on this connection
    cursor = conn.cursor()
    cursor.executescript(
        """
        CREATE TABLE contributions (
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

        CREATE TABLE warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            moderator_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );

        CREATE TABLE moderation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER,
            moderator_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            reason TEXT,
            details TEXT,
            timestamp TEXT NOT NULL
        );

        CREATE TABLE club_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        );

        CREATE TABLE member_roles (
            user_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            assigned_at TEXT NOT NULL,
            assigned_by INTEGER NOT NULL,
            PRIMARY KEY (user_id, role_id),
            FOREIGN KEY (role_id) REFERENCES club_roles(id) ON DELETE CASCADE
        );

        CREATE TABLE departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        );

        CREATE TABLE department_roles (
            department_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY (department_id, role_id),
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
            FOREIGN KEY (role_id) REFERENCES club_roles(id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    return conn


def test_contribution_create_and_update_status() -> None:
    conn = _init_in_memory()
    try:
        c = queries.create_contribution(
            conn,
            user_id=123,
            username="user#0001",
            description="Did a thing",
            links=None,
            timestamp="2026-01-01T00:00:00+00:00",
        )
        assert c.id is not None
        assert c.status == "pending"
        assert c.approved is False

        updated = queries.update_contribution_status(
            conn,
            contribution_id=int(c.id),
            status="approved",
            approved=True,
            reviewer_id=999,
            reviewed_at="2026-01-02T00:00:00+00:00",
        )
        assert updated is not None
        assert updated.status == "approved"
        assert updated.approved is True
        assert updated.reviewed_by == 999
    finally:
        conn.close()


def test_moderation_logs_list() -> None:
    conn = _init_in_memory()
    try:
        queries.add_moderation_log(
            conn,
            guild_id=1,
            user_id=10,
            moderator_id=20,
            action="warn",
            reason="be nice",
            details="warning_id=1",
            timestamp="2026-01-01T00:00:00+00:00",
        )
        queries.add_moderation_log(
            conn,
            guild_id=1,
            user_id=None,
            moderator_id=20,
            action="clear",
            reason=None,
            details="amount=10",
            timestamp="2026-01-01T01:00:00+00:00",
        )

        logs = queries.list_moderation_logs(conn, guild_id=1, limit=10)
        assert len(logs) == 2
        assert logs[0].action == "clear"

        user_logs = queries.list_moderation_logs(conn, guild_id=1, user_id=10, limit=10)
        assert len(user_logs) == 1
        assert user_logs[0].action == "warn"
    finally:
        conn.close()


def test_get_counts() -> None:
    conn = _init_in_memory()
    try:
        counts = queries.get_counts(conn)
        assert counts["contributions"] == 0
        assert counts["warnings"] == 0
    finally:
        conn.close()
