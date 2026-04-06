from __future__ import annotations

import os
from collections.abc import Callable, Coroutine
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from database import db, queries


def owner_only() -> Callable[
    [Callable[..., Coroutine[Any, Any, Any]]], Callable[..., Coroutine[Any, Any, Any]]
]:
    async def predicate(interaction: discord.Interaction) -> bool:
        is_owner = await interaction.client.is_owner(interaction.user)  # type: ignore[attr-defined]
        if not is_owner:
            raise app_commands.CheckFailure("You do not have permission to use this command.")
        return True

    return app_commands.check(predicate)


def setup_admin_commands(bot: commands.Bot) -> None:
    tree = bot.tree

    admin_group = app_commands.Group(
        name="admin",
        description="Owner-only diagnostics and maintenance commands.",
    )

    @admin_group.command(
        name="ping",
        description="Show bot latency.",
    )
    @owner_only()
    async def admin_ping(interaction: discord.Interaction) -> None:
        latency_ms = int(getattr(interaction.client, "latency", 0) * 1000)
        await interaction.response.send_message(
            f"Pong! Latency: **{latency_ms}ms**", ephemeral=True
        )

    @admin_group.command(
        name="db-path",
        description="Show the resolved SQLite database path.",
    )
    @owner_only()
    async def admin_db_path(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f"Database path: `{os.getenv('DATABASE_PATH', 'club_bot.db')}`",
            ephemeral=True,
        )

    @admin_group.command(
        name="stats",
        description="Show basic database stats.",
    )
    @owner_only()
    async def admin_stats(interaction: discord.Interaction) -> None:
        conn = db.get_connection()
        try:
            counts = queries.get_counts(conn)
        finally:
            conn.close()

        embed = discord.Embed(
            title="Bot stats",
            color=discord.Color.blurple(),
        )
        for table, count in counts.items():
            embed.add_field(name=table, value=str(count), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    tree.add_command(admin_group)
