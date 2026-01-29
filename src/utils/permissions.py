from __future__ import annotations

from typing import Callable, Coroutine, Any

import discord
from discord import app_commands

import config


def _has_named_role(member: discord.abc.Snowflake, role_name: str) -> bool:
    """Return True if the given member has a role with the provided name."""
    if not isinstance(member, discord.Member):
        return False
    return any(role.name == role_name for role in member.roles)


def hr_only() -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], Callable[..., Coroutine[Any, Any, Any]]]:
    """
    App command check ensuring the invoker has the HR role.

    The role name is provided via the HR_ROLE_NAME variable in the .env file.
    """

    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            raise app_commands.CheckFailure("This command can only be used in a server.")

        if not _has_named_role(interaction.user, config.HR_ROLE_NAME):
            raise app_commands.CheckFailure("You do not have permission to use this HR command.")

        return True

    return app_commands.check(predicate)


def staff_only() -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], Callable[..., Coroutine[Any, Any, Any]]]:
    """
    App command check ensuring the invoker has the Staff role.

    The role name is provided via the STAFF_ROLE_NAME variable in the .env file.
    """

    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            raise app_commands.CheckFailure("This command can only be used in a server.")

        if not _has_named_role(interaction.user, config.STAFF_ROLE_NAME) and not _has_named_role(
            interaction.user, config.HR_ROLE_NAME
        ):
            # HR is considered staff as well
            raise app_commands.CheckFailure("You do not have permission to use this staff command.")

        return True

    return app_commands.check(predicate)


