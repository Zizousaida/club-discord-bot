from __future__ import annotations

from typing import Iterable, List, Optional

import sqlite3

from .models import Contribution, Warning, ModerationLog, ClubRole, MemberRole


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


# ---------------------------------------------------------------------------
# Club role queries
# ---------------------------------------------------------------------------


def _row_to_club_role(row: sqlite3.Row) -> ClubRole:
    return ClubRole(
        id=row["id"],
        name=row["name"],
        description=row["description"],
    )


def create_club_role(
    conn: sqlite3.Connection,
    *,
    name: str,
    description: Optional[str],
) -> ClubRole:
    """Create a new club role."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO club_roles (name, description)
        VALUES (?, ?)
        """,
        (name, description),
    )
    conn.commit()
    role_id = cursor.lastrowid
    return get_club_role_by_id(conn, role_id)


def get_club_role_by_id(
    conn: sqlite3.Connection, role_id: int
) -> Optional[ClubRole]:
    """Get a club role by its ID."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM club_roles WHERE id = ?",
        (role_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return _row_to_club_role(row)


def get_club_role_by_name(
    conn: sqlite3.Connection, name: str
) -> Optional[ClubRole]:
    """Get a club role by its name."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM club_roles WHERE name = ?",
        (name,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return _row_to_club_role(row)


def list_all_club_roles(conn: sqlite3.Connection) -> List[ClubRole]:
    """List all club roles."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM club_roles ORDER BY name ASC"
    )
    rows = cursor.fetchall()
    return [_row_to_club_role(row) for row in rows]


def delete_club_role(
    conn: sqlite3.Connection, role_id: int
) -> bool:
    """
    Delete a club role by ID.

    Returns True if a role was deleted, False if it didn't exist.
    Note: This will cascade delete all member_roles entries due to foreign key.
    """
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM club_roles WHERE id = ?",
        (role_id,),
    )
    conn.commit()
    return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Member role assignment queries
# ---------------------------------------------------------------------------


def _row_to_member_role(row: sqlite3.Row) -> MemberRole:
    return MemberRole(
        user_id=row["user_id"],
        role_id=row["role_id"],
        assigned_at=row["assigned_at"],
        assigned_by=row["assigned_by"],
    )


def assign_role_to_member(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    role_id: int,
    assigned_by: int,
    assigned_at: str,
) -> MemberRole:
    """Assign a club role to a member."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO member_roles (user_id, role_id, assigned_at, assigned_by)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, role_id, assigned_at, assigned_by),
    )
    conn.commit()
    return get_member_role(conn, user_id=user_id, role_id=role_id)


def get_member_role(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    role_id: int,
) -> Optional[MemberRole]:
    """Get a specific member-role assignment."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM member_roles
        WHERE user_id = ? AND role_id = ?
        """,
        (user_id, role_id),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return _row_to_member_role(row)


def remove_role_from_member(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    role_id: int,
) -> bool:
    """
    Remove a club role from a member.

    Returns True if an assignment was removed, False if it didn't exist.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM member_roles
        WHERE user_id = ? AND role_id = ?
        """,
        (user_id, role_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def get_roles_for_member(
    conn: sqlite3.Connection,
    user_id: int,
) -> List[ClubRole]:
    """Get all club roles assigned to a specific member."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT cr.* FROM club_roles cr
        INNER JOIN member_roles mr ON cr.id = mr.role_id
        WHERE mr.user_id = ?
        ORDER BY cr.name ASC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    return [_row_to_club_role(row) for row in rows]


def get_members_with_role(
    conn: sqlite3.Connection,
    role_id: int,
) -> List[int]:
    """Get all user IDs that have a specific club role."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT user_id FROM member_roles
        WHERE role_id = ?
        ORDER BY assigned_at ASC
        """,
        (role_id,),
    )
    rows = cursor.fetchall()
    return [row["user_id"] for row in rows]


