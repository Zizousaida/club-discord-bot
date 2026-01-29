from __future__ import annotations

from typing import List, Optional

from database import db
from database import queries
from database.models import Contribution
from utils.time import utcnow_iso


class ContributionService:
    """
    Service layer for contribution-related operations.

    This encapsulates all database access so that commands and views
    do not need to deal with SQL directly.
    """

    def submit_contribution(
        self,
        *,
        user_id: int,
        username: str,
        description: str,
        links: Optional[str],
    ) -> Contribution:
        """Create and store a new contribution."""
        conn = db.get_connection()
        try:
            return queries.create_contribution(
                conn,
                user_id=user_id,
                username=username,
                description=description,
                links=links,
                timestamp=utcnow_iso(),
            )
        finally:
            conn.close()

    def list_user_contributions(
        self,
        *,
        user_id: int,
        limit: Optional[int] = None,
    ) -> List[Contribution]:
        """Return contributions submitted by a specific user."""
        conn = db.get_connection()
        try:
            return queries.get_contributions_by_user(
                conn,
                user_id=user_id,
                limit=limit,
            )
        finally:
            conn.close()

    def list_all_contributions(
        self,
        *,
        limit: Optional[int] = None,
    ) -> List[Contribution]:
        """Return all contributions in the system."""
        conn = db.get_connection()
        try:
            return queries.get_all_contributions(conn, limit=limit)
        finally:
            conn.close()

    def list_latest_contributions(
        self,
        *,
        limit: int = 10,
    ) -> List[Contribution]:
        """Return the latest contributions."""
        conn = db.get_connection()
        try:
            return queries.get_latest_contributions(conn, limit=limit)
        finally:
            conn.close()

    def list_pending_contributions(self) -> List[Contribution]:
        """Return all contributions that are still pending review."""
        conn = db.get_connection()
        try:
            return queries.list_pending_contributions(conn)
        finally:
            conn.close()

    def approve_contribution(
        self,
        *,
        contribution_id: int,
        reviewer_id: int,
    ) -> Optional[Contribution]:
        """Mark a contribution as approved."""
        conn = db.get_connection()
        try:
            return queries.update_contribution_status(
                conn,
                contribution_id=contribution_id,
                status="approved",
                approved=True,
                reviewer_id=reviewer_id,
                reviewed_at=utcnow_iso(),
            )
        finally:
            conn.close()

    def reject_contribution(
        self,
        *,
        contribution_id: int,
        reviewer_id: int,
    ) -> Optional[Contribution]:
        """Mark a contribution as rejected."""
        conn = db.get_connection()
        try:
            return queries.update_contribution_status(
                conn,
                contribution_id=contribution_id,
                status="rejected",
                approved=False,
                reviewer_id=reviewer_id,
                reviewed_at=utcnow_iso(),
            )
        finally:
            conn.close()


