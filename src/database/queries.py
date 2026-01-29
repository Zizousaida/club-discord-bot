from __future__ import annotations

from typing import Iterable, List, Optional

import sqlite3

from .models import Contribution, Warning, ModerationLog


# ---------------------------------------------------------------------------
# Contribution queries
# ---------------------------------------------------------------------------


def create_contribution(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    username: str,
    description: str,
    links: Optional[str],
    timestamp: str,
) -> Contribution:
    """Insert a new contribution into the database."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO contributions (
            user_id, username, description, links, timestamp, approved, status
        ) VALUES (?, ?, ?, ?, ?, 0, 'pending')
        """,
        (user_id, username, description, links, timestamp),
    )
    conn.commit()
    contribution_id = cursor.lastrowid
    return get_contribution_by_id(conn, contribution_id)


def _row_to_contribution(row: sqlite3.Row) -> Contribution:
    return Contribution(
        id=row["id"],
        user_id=row["user_id"],
        username=row["username"],
        description=row["description"],
        links=row["links"],
        timestamp=row["timestamp"],
        approved=bool(row["approved"]),
        status=row["status"],
        reviewed_by=row["reviewed_by"],
        reviewed_at=row["reviewed_at"],
    )


def get_contribution_by_id(
    conn: sqlite3.Connection, contribution_id: int
) -> Optional[Contribution]:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM contributions WHERE id = ?",
        (contribution_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return _row_to_contribution(row)


def get_contributions_by_user(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    limit: Optional[int] = None,
) -> List[Contribution]:
    sql = "SELECT * FROM contributions WHERE user_id = ? ORDER BY timestamp DESC"
    params: Iterable[object] = (user_id,)
    if limit is not None:
        sql += " LIMIT ?"
        params = (user_id, limit)

    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    return [_row_to_contribution(row) for row in rows]


def get_all_contributions(
    conn: sqlite3.Connection,
    *,
    limit: Optional[int] = None,
) -> List[Contribution]:
    sql = "SELECT * FROM contributions ORDER BY timestamp DESC"
    params: Iterable[object] = ()
    if limit is not None:
        sql += " LIMIT ?"
        params = (limit,)

    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    return [_row_to_contribution(row) for row in rows]


def get_latest_contributions(
    conn: sqlite3.Connection,
    *,
    limit: int = 10,
) -> List[Contribution]:
    return get_all_contributions(conn, limit=limit)


def list_pending_contributions(
    conn: sqlite3.Connection,
) -> List[Contribution]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM contributions
        WHERE status = 'pending'
        ORDER BY timestamp DESC
        """
    )
    rows = cursor.fetchall()
    return [_row_to_contribution(row) for row in rows]


def update_contribution_status(
    conn: sqlite3.Connection,
    *,
    contribution_id: int,
    status: str,
    approved: bool,
    reviewer_id: int,
    reviewed_at: str,
) -> Optional[Contribution]:
    """
    Update the status of a contribution (approved / rejected).

    Returns the updated contribution, or None if it does not exist.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE contributions
        SET status = ?, approved = ?, reviewed_by = ?, reviewed_at = ?
        WHERE id = ?
        """,
        (status, int(approved), reviewer_id, reviewed_at, contribution_id),
    )
    if cursor.rowcount == 0:
        return None

    conn.commit()
    return get_contribution_by_id(conn, contribution_id)


# ---------------------------------------------------------------------------
# Warning queries
# ---------------------------------------------------------------------------


def _row_to_warning(row: sqlite3.Row) -> Warning:
    return Warning(
        id=row["id"],
        guild_id=row["guild_id"],
        user_id=row["user_id"],
        moderator_id=row["moderator_id"],
        reason=row["reason"],
        timestamp=row["timestamp"],
    )


def add_warning(
    conn: sqlite3.Connection,
    *,
    guild_id: int,
    user_id: int,
    moderator_id: int,
    reason: str,
    timestamp: str,
) -> Warning:
    """Insert a new warning for a user."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO warnings (
            guild_id, user_id, moderator_id, reason, timestamp
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (guild_id, user_id, moderator_id, reason, timestamp),
    )
    conn.commit()
    warning_id = cursor.lastrowid
    return get_warning_by_id(conn, warning_id)


def get_warning_by_id(
    conn: sqlite3.Connection, warning_id: int
) -> Optional[Warning]:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM warnings WHERE id = ?",
        (warning_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return _row_to_warning(row)


def get_warnings_for_user(
    conn: sqlite3.Connection,
    *,
    guild_id: int,
    user_id: int,
) -> List[Warning]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM warnings
        WHERE guild_id = ? AND user_id = ?
        ORDER BY timestamp DESC
        """,
        (guild_id, user_id),
    )
    rows = cursor.fetchall()
    return [_row_to_warning(row) for row in rows]


# ---------------------------------------------------------------------------
# Moderation log queries
# ---------------------------------------------------------------------------


def _row_to_moderation_log(row: sqlite3.Row) -> ModerationLog:
    return ModerationLog(
        id=row["id"],
        guild_id=row["guild_id"],
        user_id=row["user_id"],
        moderator_id=row["moderator_id"],
        action=row["action"],
        reason=row["reason"],
        details=row["details"],
        timestamp=row["timestamp"],
    )


def add_moderation_log(
    conn: sqlite3.Connection,
    *,
    guild_id: int,
    user_id: Optional[int],
    moderator_id: int,
    action: str,
    reason: Optional[str],
    details: Optional[str],
    timestamp: str,
) -> ModerationLog:
    """Insert a new moderation log entry."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO moderation_logs (
            guild_id, user_id, moderator_id, action, reason, details, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (guild_id, user_id, moderator_id, action, reason, details, timestamp),
    )
    conn.commit()
    log_id = cursor.lastrowid
    return get_moderation_log_by_id(conn, log_id)


def get_moderation_log_by_id(
    conn: sqlite3.Connection, log_id: int
) -> Optional[ModerationLog]:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM moderation_logs WHERE id = ?",
        (log_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return _row_to_moderation_log(row)


