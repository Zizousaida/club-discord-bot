from __future__ import annotations

import logging
from typing import Any

import discord
from discord.ext import commands

import config
from commands.admin import setup_admin_commands
from commands.contribution import setup_contribution_commands
from commands.export import setup_export_commands
from commands.help import setup_help_command
from commands.moderation import setup_moderation_commands
from commands.roles import setup_role_commands
from database.db import init_db
from services.contribution_service import ContributionService
from services.role_service import RoleService

log = logging.getLogger(__name__)


def _configure_response_visibility() -> None:
    """
    Force command responses to be public when configured.

    This centralizes visibility behavior so command modules do not need
    to manage `ephemeral` flags individually.
    """
    if not config.COMMAND_RESPONSES_PUBLIC:
        return

    response_cls: Any = discord.InteractionResponse
    if getattr(response_cls, "_club_visibility_patched", False):
        return

    original_send_message = discord.InteractionResponse.send_message
    original_defer = discord.InteractionResponse.defer
    original_webhook_send = discord.Webhook.send

    async def send_message_public(self, *args, **kwargs):
        kwargs["ephemeral"] = False
        return await original_send_message(self, *args, **kwargs)

    async def defer_public(self, *args, **kwargs):
        kwargs["ephemeral"] = False
        return await original_defer(self, *args, **kwargs)

    async def webhook_send_public(self, *args, **kwargs):
        kwargs["ephemeral"] = False
        return await original_webhook_send(self, *args, **kwargs)

    discord.InteractionResponse.send_message = send_message_public  # type: ignore[method-assign]
    discord.InteractionResponse.defer = defer_public  # type: ignore[method-assign]
    discord.Webhook.send = webhook_send_public  # type: ignore[method-assign]
    response_cls._club_visibility_patched = True


class ClubBot(commands.Bot):
    """
    Main Discord bot entry point.

    This subclass wires together:
    - database initialization
    - app command (slash command) registration
    - shared services
    """

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = False

        super().__init__(
            command_prefix="!",  # prefix is unused, we only use slash commands
            intents=intents,
            help_command=None,
        )

        # Shared service instances
        self.contribution_service = ContributionService()
        self.role_service = RoleService()

    async def setup_hook(self) -> None:
        """
        Called by discord.py when the bot starts.

        We sync the app commands here and initialize any background tasks.
        """
        # Initialize the database schema
        init_db()
        _configure_response_visibility()

        # Register slash commands
        setup_contribution_commands(self)
        setup_moderation_commands(self)
        setup_role_commands(self)
        setup_help_command(self)
        setup_admin_commands(self)
        setup_export_commands(self)

        # Log all registered commands for debugging
        all_commands = [cmd.name for cmd in self.tree.get_commands()]
        log.info("Registered commands: %s", ", ".join(all_commands))

        guild_id = config.get_guild_id()
        if guild_id:
            # Faster development: sync commands to a single guild
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("Synced %d commands to guild %s", len(synced), guild_id)
            for cmd in synced:
                log.debug("Synced command: %s", cmd.name)
        else:
            synced = await self.tree.sync()
            log.info("Synced %d global commands", len(synced))
            for cmd in synced:
                log.debug("Synced command: %s", cmd.name)

    async def on_ready(self) -> None:
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id if self.user else "unknown")
        await self.change_presence(
            activity=discord.Game(name="/contribute | /warn"),
        )


def create_bot() -> ClubBot:
    """Factory function used by run.py to create the bot instance."""
    return ClubBot()
