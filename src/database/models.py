from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Contribution:
    """Represents a contribution submitted by a member."""

    id: Optional[int]
    user_id: int
    username: str
    description: str
    links: Optional[str]
    timestamp: str
    approved: bool
    status: str
    reviewed_by: Optional[int]
    reviewed_at: Optional[str]


@dataclass
class Warning:
    """Represents a moderation warning issued to a user."""

    id: Optional[int]
    guild_id: int
    user_id: int
    moderator_id: int
    reason: str
    timestamp: str


@dataclass
class ModerationLog:
    """Represents a generic moderation log entry."""

    id: Optional[int]
    guild_id: int
    user_id: Optional[int]
    moderator_id: int
    action: str
    reason: Optional[str]
    details: Optional[str]
    timestamp: str


