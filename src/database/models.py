from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Contribution:
    """Represents a contribution submitted by a member."""

    id: int | None
    user_id: int
    username: str
    description: str
    links: str | None
    timestamp: str
    approved: bool
    status: str
    reviewed_by: int | None
    reviewed_at: str | None


@dataclass
class Warning:
    """Represents a moderation warning issued to a user."""

    id: int | None
    guild_id: int
    user_id: int
    moderator_id: int
    reason: str
    timestamp: str


@dataclass
class ModerationLog:
    """Represents a generic moderation log entry."""

    id: int | None
    guild_id: int
    user_id: int | None
    moderator_id: int
    action: str
    reason: str | None
    details: str | None
    timestamp: str


@dataclass
class ClubRole:
    """Represents an organizational role within the club."""

    id: int | None
    name: str
    description: str | None


@dataclass
class MemberRole:
    """Represents a member's assignment to a club role."""

    user_id: int
    role_id: int
    assigned_at: str
    assigned_by: int


@dataclass
class Department:
    """Represents a department that groups club roles."""

    id: int | None
    name: str
    description: str | None
