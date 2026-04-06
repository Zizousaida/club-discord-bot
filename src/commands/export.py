from __future__ import annotations

import csv
import io

import discord
from discord import app_commands
from discord.ext import commands

from database import db, queries
from utils.permissions import hr_only, staff_only


def setup_export_commands(bot: commands.Bot) -> None:
    tree = bot.tree

    export_group = app_commands.Group(
        name="export",
        description="Export bot data (CSV).",
    )

    @export_group.command(
        name="contributions",
        description="Export contributions to a CSV file.",
    )
    @hr_only()
    async def export_contributions(
        interaction: discord.Interaction,
        member: discord.Member | None = None,
        limit: app_commands.Range[int, 1, 500] = 200,
    ) -> None:
        conn = db.get_connection()
        try:
            if member:
                rows = queries.get_contributions_by_user(conn, member.id, limit=limit)
                filename = f"contributions_{member.id}.csv"
            else:
                rows = queries.get_all_contributions(conn, limit=limit)
                filename = "contributions.csv"
        finally:
            conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "id",
                "user_id",
                "username",
                "timestamp",
                "status",
                "approved",
                "reviewed_by",
                "reviewed_at",
                "description",
                "links",
            ]
        )
        for c in rows:
            writer.writerow(
                [
                    c.id,
                    c.user_id,
                    c.username,
                    c.timestamp,
                    c.status,
                    int(c.approved),
                    c.reviewed_by,
                    c.reviewed_at,
                    c.description,
                    c.links or "",
                ]
            )

        data = io.BytesIO(output.getvalue().encode("utf-8"))
        await interaction.response.send_message(
            "Here’s your export.",
            file=discord.File(fp=data, filename=filename),
            ephemeral=True,
        )

    @export_group.command(
        name="warnings",
        description="Export warnings for a member to a CSV file.",
    )
    @staff_only()
    async def export_warnings(
        interaction: discord.Interaction,
        member: discord.Member,
    ) -> None:
        if not interaction.guild_id:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        conn = db.get_connection()
        try:
            warns = queries.get_warnings_for_user(
                conn,
                guild_id=interaction.guild_id,
                user_id=member.id,
            )
        finally:
            conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "guild_id", "user_id", "moderator_id", "timestamp", "reason"])
        for w in warns:
            writer.writerow([w.id, w.guild_id, w.user_id, w.moderator_id, w.timestamp, w.reason])

        data = io.BytesIO(output.getvalue().encode("utf-8"))
        await interaction.response.send_message(
            "Here’s your export.",
            file=discord.File(fp=data, filename=f"warnings_{interaction.guild_id}_{member.id}.csv"),
            ephemeral=True,
        )

    tree.add_command(export_group)
