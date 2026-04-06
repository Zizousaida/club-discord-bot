from __future__ import annotations

from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

import config
from database import db, queries
from utils.permissions import staff_only
from utils.time import utcnow_iso


async def _send_mod_log(
    guild: discord.Guild,
    *,
    embed: discord.Embed,
) -> None:
    """Send a moderation log embed to the configured log channel, if set."""
    log_channel_id = config.get_log_channel_id()
    if not log_channel_id:
        return

    channel = guild.get_channel(log_channel_id)
    if isinstance(channel, (discord.TextChannel, discord.Thread)):
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            # If we cannot send logs, silently ignore to avoid breaking commands.
            return


def setup_moderation_commands(bot: commands.Bot) -> None:
    """
    Register moderation-related slash commands on the bot's app command tree.

    Implemented commands:
    - /mute
    - /unmute
    - /warn
    - /warnings
    - /clear
    - /modlogs
    """

    tree = bot.tree

    @app_commands.command(
        name="mute",
        description="Temporarily timeout a member.",
    )
    @staff_only()
    @app_commands.describe(
        member="Member to mute",
        duration_minutes="Duration of the timeout in minutes",
        reason="Reason for the mute",
    )
    async def mute(
        interaction: discord.Interaction,
        member: discord.Member,
        duration_minutes: app_commands.Range[int, 1, 10080],
        reason: str | None = None,
    ) -> None:
        if member == interaction.user:
            await interaction.response.send_message(
                "You cannot mute yourself.",
                ephemeral=True,
            )
            return

        until = discord.utils.utcnow() + timedelta(minutes=duration_minutes)

        try:
            await member.timeout(until, reason=reason or "Muted by staff")
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have permission to mute that member.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"🔇 {member.mention} has been muted for {duration_minutes} minutes.",
            ephemeral=True,
        )

        # Record moderation log and DB entry
        conn = db.get_connection()
        try:
            queries.add_moderation_log(
                conn,
                guild_id=interaction.guild_id or 0,
                user_id=member.id,
                moderator_id=interaction.user.id,
                action="mute",
                reason=reason,
                details=f"duration_minutes={duration_minutes}",
                timestamp=utcnow_iso(),
            )
        finally:
            conn.close()

        if interaction.guild:
            embed = discord.Embed(
                title="Member muted",
                description=f"{member.mention} was muted by {interaction.user.mention}",
                color=discord.Color.red(),
            )
            embed.add_field(name="Duration", value=f"{duration_minutes} minutes", inline=True)
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            await _send_mod_log(interaction.guild, embed=embed)

    tree.add_command(mute)

    @app_commands.command(
        name="unmute",
        description="Remove timeout from a member.",
    )
    @staff_only()
    @app_commands.describe(
        member="Member to unmute",
        reason="Reason for unmuting",
    )
    async def unmute(
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str | None = None,
    ) -> None:
        try:
            await member.timeout(None, reason=reason or "Unmuted by staff")
        except discord.Forbidden:
            await interaction.response.send_message(
                "I do not have permission to unmute that member.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"🔊 {member.mention} has been unmuted.",
            ephemeral=True,
        )

        conn = db.get_connection()
        try:
            queries.add_moderation_log(
                conn,
                guild_id=interaction.guild_id or 0,
                user_id=member.id,
                moderator_id=interaction.user.id,
                action="unmute",
                reason=reason,
                details=None,
                timestamp=utcnow_iso(),
            )
        finally:
            conn.close()

        if interaction.guild:
            embed = discord.Embed(
                title="Member unmuted",
                description=f"{member.mention} was unmuted by {interaction.user.mention}",
                color=discord.Color.green(),
            )
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            await _send_mod_log(interaction.guild, embed=embed)

    tree.add_command(unmute)

    @app_commands.command(
        name="warn",
        description="Issue a warning to a member.",
    )
    @staff_only()
    @app_commands.describe(
        member="Member to warn",
        reason="Reason for the warning",
    )
    async def warn(
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str,
    ) -> None:
        if member == interaction.user:
            await interaction.response.send_message(
                "You cannot warn yourself.",
                ephemeral=True,
            )
            return

        conn = db.get_connection()
        try:
            warning = queries.add_warning(
                conn,
                guild_id=interaction.guild_id or 0,
                user_id=member.id,
                moderator_id=interaction.user.id,
                reason=reason,
                timestamp=utcnow_iso(),
            )
            queries.add_moderation_log(
                conn,
                guild_id=interaction.guild_id or 0,
                user_id=member.id,
                moderator_id=interaction.user.id,
                action="warn",
                reason=reason,
                details=f"warning_id={warning.id}",
                timestamp=utcnow_iso(),
            )
        finally:
            conn.close()

        await interaction.response.send_message(
            f"⚠️ {member.mention} has been warned. Reason: {reason}",
            ephemeral=True,
        )

        if interaction.guild:
            embed = discord.Embed(
                title="Member warned",
                description=f"{member.mention} was warned by {interaction.user.mention}",
                color=discord.Color.orange(),
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            await _send_mod_log(interaction.guild, embed=embed)

    tree.add_command(warn)

    @app_commands.command(
        name="warnings",
        description="View warnings for a member.",
    )
    @staff_only()
    @app_commands.describe(
        member="Member whose warnings to view",
    )
    async def warnings(
        interaction: discord.Interaction,
        member: discord.Member,
    ) -> None:
        conn = db.get_connection()
        try:
            warns = queries.get_warnings_for_user(
                conn,
                guild_id=interaction.guild_id or 0,
                user_id=member.id,
            )
        finally:
            conn.close()

        if not warns:
            await interaction.response.send_message(
                f"{member.mention} has no recorded warnings.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"Warnings for {member}",
            color=discord.Color.orange(),
        )
        for w in warns[:25]:
            embed.add_field(
                name=f"Warning #{w.id}",
                value=f"Issued by <@{w.moderator_id}> at {w.timestamp}\nReason: {w.reason}",
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    tree.add_command(warnings)

    @app_commands.command(
        name="clear",
        description="Bulk delete a number of recent messages from the current channel.",
    )
    @staff_only()
    @app_commands.describe(
        amount="Number of recent messages to delete (max 100).",
    )
    async def clear(
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 1, 100],
    ) -> None:
        if not isinstance(interaction.channel, (discord.TextChannel, discord.Thread)):
            await interaction.response.send_message(
                "This command can only be used in text channels.",
                ephemeral=True,
            )
            return

        # Defer since deleting messages can take a moment
        await interaction.response.defer(ephemeral=True)

        deleted = await interaction.channel.purge(limit=amount + 1)  # include the command message

        await interaction.followup.send(
            f"🧹 Deleted {len(deleted) - 1} messages.",
            ephemeral=True,
        )

        conn = db.get_connection()
        try:
            queries.add_moderation_log(
                conn,
                guild_id=interaction.guild_id or 0,
                user_id=None,
                moderator_id=interaction.user.id,
                action="clear",
                reason=None,
                details=f"amount={amount}",
                timestamp=utcnow_iso(),
            )
        finally:
            conn.close()

        if interaction.guild:
            embed = discord.Embed(
                title="Messages cleared",
                description=f"{interaction.user.mention} cleared {len(deleted) - 1} messages in {interaction.channel.mention}.",
                color=discord.Color.blurple(),
            )
            await _send_mod_log(interaction.guild, embed=embed)

    tree.add_command(clear)

    @app_commands.command(
        name="modlogs",
        description="View recent moderation log entries.",
    )
    @staff_only()
    @app_commands.describe(
        member="Optional member to filter logs for",
        limit="Max entries to show (1-25)",
    )
    async def modlogs(
        interaction: discord.Interaction,
        member: discord.Member | None = None,
        limit: app_commands.Range[int, 1, 25] = 10,
    ) -> None:
        if not interaction.guild_id:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        conn = db.get_connection()
        try:
            logs = queries.list_moderation_logs(
                conn,
                guild_id=interaction.guild_id,
                user_id=member.id if member else None,
                limit=limit,
            )
        finally:
            conn.close()

        if not logs:
            await interaction.response.send_message(
                "No moderation logs found for that filter.",
                ephemeral=True,
            )
            return

        title = "Moderation logs"
        if member:
            title = f"Moderation logs for {member}"

        embed = discord.Embed(
            title=title,
            color=discord.Color.blurple(),
        )

        for entry in logs:
            who = f"<@{entry.user_id}>" if entry.user_id else "N/A"
            reason = entry.reason or "—"
            details = entry.details or "—"
            embed.add_field(
                name=f"{entry.action} • {entry.timestamp}",
                value=f"User: {who}\nModerator: <@{entry.moderator_id}>\nReason: {reason}\nDetails: {details}",
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    tree.add_command(modlogs)
