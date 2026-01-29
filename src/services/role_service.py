from __future__ import annotations

from typing import List, Optional

from database import db
from database import queries
from database.models import ClubRole, MemberRole
from utils.time import utcnow_iso


class RoleService:
    """
    Service layer for club role management operations.

    This encapsulates all database access so that commands
    do not need to deal with SQL directly.
    """

    def create_role(
        self,
        *,
        name: str,
        description: Optional[str],
    ) -> ClubRole:
        """Create a new club role."""
        conn = db.get_connection()
        try:
            return queries.create_club_role(
                conn,
                name=name,
                description=description,
            )
        finally:
            conn.close()

    def get_role_by_name(self, name: str) -> Optional[ClubRole]:
        """Get a club role by its name."""
        conn = db.get_connection()
        try:
            return queries.get_club_role_by_name(conn, name)
        finally:
            conn.close()

    def get_role_by_id(self, role_id: int) -> Optional[ClubRole]:
        """Get a club role by its ID."""
        conn = db.get_connection()
        try:
            return queries.get_club_role_by_id(conn, role_id)
        finally:
            conn.close()

    def list_all_roles(self) -> List[ClubRole]:
        """List all club roles."""
        conn = db.get_connection()
        try:
            return queries.list_all_club_roles(conn)
        finally:
            conn.close()

    def delete_role(self, role_id: int) -> bool:
        """
        Delete a club role by ID.

        Returns True if the role was deleted, False if it didn't exist.
        This will also remove all member assignments to this role.
        """
        conn = db.get_connection()
        try:
            return queries.delete_club_role(conn, role_id)
        finally:
            conn.close()

    def assign_role(
        self,
        *,
        user_id: int,
        role_id: int,
        assigned_by: int,
    ) -> MemberRole:
        """Assign a club role to a member."""
        conn = db.get_connection()
        try:
            return queries.assign_role_to_member(
                conn,
                user_id=user_id,
                role_id=role_id,
                assigned_by=assigned_by,
                assigned_at=utcnow_iso(),
            )
        finally:
            conn.close()

    def remove_role(
        self,
        *,
        user_id: int,
        role_id: int,
    ) -> bool:
        """
        Remove a club role from a member.

        Returns True if the assignment was removed, False if it didn't exist.
        """
        conn = db.get_connection()
        try:
            return queries.remove_role_from_member(
                conn,
                user_id=user_id,
                role_id=role_id,
            )
        finally:
            conn.close()

    def get_member_roles(self, user_id: int) -> List[ClubRole]:
        """Get all club roles assigned to a specific member."""
        conn = db.get_connection()
        try:
            return queries.get_roles_for_member(conn, user_id)
        finally:
            conn.close()

    def get_role_members(self, role_id: int) -> List[int]:
        """Get all user IDs that have a specific club role."""
        conn = db.get_connection()
        try:
            return queries.get_members_with_role(conn, role_id)
        finally:
            conn.close()

    def is_member_assigned(
        self,
        *,
        user_id: int,
        role_id: int,
    ) -> bool:
        """Check if a member is assigned to a specific role."""
        conn = db.get_connection()
        try:
            assignment = queries.get_member_role(
                conn,
                user_id=user_id,
                role_id=role_id,
            )
            return assignment is not None
        finally:
            conn.close()

