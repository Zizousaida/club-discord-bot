import os
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from a .env file in the project root.
# Copy .env.example to .env and fill in the values before running the bot.
load_dotenv()


def _get_int(name: str, default: int = 0) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


# Discord bot token
DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")

# Human Resources and Staff role names used for permission checks
HR_ROLE_NAME: str = os.getenv("HR_ROLE_NAME", "HR")
STAFF_ROLE_NAME: str = os.getenv("STAFF_ROLE_NAME", "Staff")

# Optional: restrict commands to a single guild for faster sync during development
GUILD_ID: int = _get_int("GUILD_ID", 0)

# Channel where moderation actions will be logged
LOG_CHANNEL_ID: int = _get_int("LOG_CHANNEL_ID", 0)

# Path to the SQLite database file
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "club_bot.db")


def get_guild_id() -> Optional[int]:
    """Return the configured guild ID, or None if not set."""
    return GUILD_ID or None


def get_log_channel_id() -> Optional[int]:
    """Return the configured moderation log channel ID, or None if not set."""
    return LOG_CHANNEL_ID or None


