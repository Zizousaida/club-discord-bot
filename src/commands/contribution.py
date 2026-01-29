from __future__ import annotations

from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from services.contribution_service import ContributionService
from utils.permissions import hr_only
from utils.time import format_timestamp_for_display
from views.contribution_modal import ContributionModal


def _get_contribution_service(bot: commands.Bot) -> ContributionService:
    service = getattr(bot, "contribution_service", None)
    if not isinstance(service, ContributionService):
        raise RuntimeError("ContributionService is not attached to the bot.")
    return service


def setup_contribution_commands(bot: commands.Bot) -> None:
    """
    Register contribution-related slash commands on the bot's app command tree.

    - /contribute: members submit contributions via a modal
    - /contributions list: HR view all contributions or by user
    - /contributions latest: HR list latest contributions
    - /contributions approve: HR approve a contribution
    - /contributions reject: HR reject a contribution
    """

    tree = bot.tree

    @app_commands.command(name="contribute", description="Submit a private contribution to the HR team.")
    async def contribute(interaction: discord.Interaction) -> None:
        service = _get_contribution_service(interaction.client)  # type: ignore[arg-type]
        modal = ContributionModal(service=service, user=interaction.user)
        await interaction.response.send_modal(modal)

    tree.add_command(contribute)

    contributions_group = app_commands.Group(
        name="contributions",
        description="HR tools for managing member contributions.",
    )

    @contributions_group.command(
        name="list",
        description="List contributions. Optionally filter by member.",
    )
    @hr_only()
    async def contributions_list(
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
        limit: app_commands.Range[int, 1, 50] = 10,
    ) -> None:
        service = _get_contribution_service(interaction.client)  # type: ignore[arg-type]

        if member is not None:
            contribs = service.list_user_contributions(user_id=member.id, limit=limit)
            title = f"Contributions by {member} (latest {len(contribs)})"
        else:
            contribs = service.list_all_contributions(limit=limit)
            title = f"All contributions (latest {len(contribs)})"

        if not contribs:
            await interaction.response.send_message(
                "No contributions found for the given criteria.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(title=title, color=discord.Color.blurple())
        for contrib in contribs:
            status = "✅ Approved" if contrib.approved else "⏳ Pending" if contrib.status == "pending" else "❌ Rejected"
            user_line = f"<@{contrib.user_id}> (`{contrib.username}`)"
            ts = format_timestamp_for_display(contrib.timestamp)
            value = f"{status} • {ts}\nID: `{contrib.id}`\n{contrib.description}"
            if contrib.links:
                value += f"\nLinks: {contrib.links}"
            embed.add_field(
                name=user_line,
                value=value[:1024],
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @contributions_group.command(
        name="latest",
        description="List the latest contributions.",
    )
    @hr_only()
    async def contributions_latest(
        interaction: discord.Interaction,
        limit: app_commands.Range[int, 1, 25] = 10,
    ) -> None:
        service = _get_contribution_service(interaction.client)  # type: ignore[arg-type]
        contribs = service.list_latest_contributions(limit=limit)

        if not contribs:
            await interaction.response.send_message(
                "There are no contributions yet.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"Latest {len(contribs)} contributions",
            color=discord.Color.blurple(),
        )
        for contrib in contribs:
            status = "✅ Approved" if contrib.approved else "⏳ Pending" if contrib.status == "pending" else "❌ Rejected"
            ts = format_timestamp_for_display(contrib.timestamp)
            value = f"{status} • {ts}\nID: `{contrib.id}`\n{contrib.description}"
            if contrib.links:
                value += f"\nLinks: {contrib.links}"
            embed.add_field(
                name=f"<@{contrib.user_id}> (`{contrib.username}`)",
                value=value[:1024],
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @contributions_group.command(
        name="approve",
        description="Approve a contribution by ID.",
    )
    @hr_only()
    async def contributions_approve(
        interaction: discord.Interaction,
        contribution_id: int,
    ) -> None:
        service = _get_contribution_service(interaction.client)  # type: ignore[arg-type]
        updated = service.approve_contribution(
            contribution_id=contribution_id,
            reviewer_id=interaction.user.id,
        )

        if not updated:
            await interaction.response.send_message(
                f"No contribution with ID `{contribution_id}` was found.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"✅ Contribution `{contribution_id}` from <@{updated.user_id}> has been approved.",
            ephemeral=True,
        )

    @contributions_group.command(
        name="reject",
        description="Reject a contribution by ID.",
    )
    @hr_only()
    async def contributions_reject(
        interaction: discord.Interaction,
        contribution_id: int,
    ) -> None:
        service = _get_contribution_service(interaction.client)  # type: ignore[arg-type]
        updated = service.reject_contribution(
            contribution_id=contribution_id,
            reviewer_id=interaction.user.id,
        )

        if not updated:
            await interaction.response.send_message(
                f"No contribution with ID `{contribution_id}` was found.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"❌ Contribution `{contribution_id}` from <@{updated.user_id}> has been rejected.",
            ephemeral=True,
        )

    tree.add_command(contributions_group)


