from __future__ import annotations

from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from services.role_service import RoleService
from utils.permissions import hr_only
from utils.time import format_timestamp_for_display


def _get_role_service(bot: commands.Bot) -> RoleService:
    """Get the RoleService instance from the bot."""
    service = getattr(bot, "role_service", None)
    if not isinstance(service, RoleService):
        raise RuntimeError("RoleService is not attached to the bot.")
    return service


def setup_role_commands(bot: commands.Bot) -> None:
    """
    Register role management slash commands on the bot's app command tree.

    Commands:
    - /role create: Create a new club role
    - /role delete: Delete a club role
    - /role assign: Assign a role to a member
    - /role remove: Remove a role from a member
    - /role list: List all club roles
    - /role members: List all members with a specific role
    - /role user: List all roles for a specific user
    """

    tree = bot.tree

    role_group = app_commands.Group(
        name="role",
        description="HR tools for managing club organizational roles.",
    )

    @role_group.command(
        name="create",
        description="Create a new club organizational role.",
    )
    @hr_only()
    @app_commands.describe(
        name="Name of the role (must be unique)",
        description="Optional description of the role",
    )
    async def role_create(
        interaction: discord.Interaction,
        name: str,
        description: Optional[str] = None,
    ) -> None:
        service = _get_role_service(interaction.client)  # type: ignore[arg-type]

        # Check if role already exists
        existing = service.get_role_by_name(name)
        if existing:
            await interaction.response.send_message(
                f"❌ A role named `{name}` already exists.",
                ephemeral=True,
            )
            return

        try:
            role = service.create_role(name=name, description=description)
            embed = discord.Embed(
                title="✅ Role Created",
                description=f"Created role `{role.name}` (ID: {role.id})",
                color=discord.Color.green(),
            )
            if role.description:
                embed.add_field(name="Description", value=role.description, inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to create role: {str(e)}",
                ephemeral=True,
            )

    @role_group.command(
        name="delete",
        description="Delete a club organizational role.",
    )
    @hr_only()
    @app_commands.describe(
        name="Name of the role to delete",
    )
    async def role_delete(
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        service = _get_role_service(interaction.client)  # type: ignore[arg-type]

        role = service.get_role_by_name(name)
        if not role:
            await interaction.response.send_message(
                f"❌ Role `{name}` not found.",
                ephemeral=True,
            )
            return

        deleted = service.delete_role(role.id)
        if deleted:
            await interaction.response.send_message(
                f"✅ Role `{name}` has been deleted. All member assignments have been removed.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ Failed to delete role `{name}`.",
                ephemeral=True,
            )

    @role_group.command(
        name="assign",
        description="Assign a club role to a member.",
    )
    @hr_only()
    @app_commands.describe(
        user="Member to assign the role to",
        role="Name of the club role",
    )
    async def role_assign(
        interaction: discord.Interaction,
        user: discord.Member,
        role: str,
    ) -> None:
        service = _get_role_service(interaction.client)  # type: ignore[arg-type]

        club_role = service.get_role_by_name(role)
        if not club_role:
            await interaction.response.send_message(
                f"❌ Role `{role}` not found.",
                ephemeral=True,
            )
            return

        # Check if already assigned
        if service.is_member_assigned(user_id=user.id, role_id=club_role.id):
            await interaction.response.send_message(
                f"❌ {user.mention} already has the role `{role}`.",
                ephemeral=True,
            )
            return

        try:
            service.assign_role(
                user_id=user.id,
                role_id=club_role.id,
                assigned_by=interaction.user.id,
            )
            embed = discord.Embed(
                title="✅ Role Assigned",
                description=f"{user.mention} has been assigned the role `{role}`.",
                color=discord.Color.green(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to assign role: {str(e)}",
                ephemeral=True,
            )

    @role_group.command(
        name="remove",
        description="Remove a club role from a member.",
    )
    @hr_only()
    @app_commands.describe(
        user="Member to remove the role from",
        role="Name of the club role",
    )
    async def role_remove(
        interaction: discord.Interaction,
        user: discord.Member,
        role: str,
    ) -> None:
        service = _get_role_service(interaction.client)  # type: ignore[arg-type]

        club_role = service.get_role_by_name(role)
        if not club_role:
            await interaction.response.send_message(
                f"❌ Role `{role}` not found.",
                ephemeral=True,
            )
            return

        # Check if assigned
        if not service.is_member_assigned(user_id=user.id, role_id=club_role.id):
            await interaction.response.send_message(
                f"❌ {user.mention} does not have the role `{role}`.",
                ephemeral=True,
            )
            return

        removed = service.remove_role(
            user_id=user.id,
            role_id=club_role.id,
        )
        if removed:
            embed = discord.Embed(
                title="✅ Role Removed",
                description=f"{user.mention} no longer has the role `{role}`.",
                color=discord.Color.orange(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                f"❌ Failed to remove role from {user.mention}.",
                ephemeral=True,
            )

    @role_group.command(
        name="list",
        description="List all club organizational roles.",
    )
    @hr_only()
    async def role_list(
        interaction: discord.Interaction,
    ) -> None:
        service = _get_role_service(interaction.client)  # type: ignore[arg-type]
        roles = service.list_all_roles()

        if not roles:
            await interaction.response.send_message(
                "No club roles have been created yet.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="Club Organizational Roles",
            color=discord.Color.blurple(),
        )

        for role in roles:
            # Get member count for this role
            members = service.get_role_members(role.id)
            member_count = len(members)
            value = f"ID: `{role.id}` • {member_count} member(s)"
            if role.description:
                value += f"\n{role.description}"
            embed.add_field(
                name=role.name,
                value=value,
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @role_group.command(
        name="members",
        description="List all members with a specific club role.",
    )
    @hr_only()
    @app_commands.describe(
        role="Name of the club role",
    )
    async def role_members(
        interaction: discord.Interaction,
        role: str,
    ) -> None:
        service = _get_role_service(interaction.client)  # type: ignore[arg-type]

        club_role = service.get_role_by_name(role)
        if not club_role:
            await interaction.response.send_message(
                f"❌ Role `{role}` not found.",
                ephemeral=True,
            )
            return

        member_ids = service.get_role_members(club_role.id)

        if not member_ids:
            await interaction.response.send_message(
                f"No members have been assigned the role `{role}`.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"Members with role: {role}",
            description=f"Total: {len(member_ids)} member(s)",
            color=discord.Color.blurple(),
        )

        # Format member mentions (Discord will resolve them)
        member_mentions = [f"<@{user_id}>" for user_id in member_ids]
        # Split into chunks if too many members
        if len(member_mentions) <= 25:
            embed.add_field(
                name="Members",
                value="\n".join(member_mentions) or "None",
                inline=False,
            )
        else:
            # Discord embed fields have limits, so split into multiple fields
            chunk_size = 20
            for i in range(0, len(member_mentions), chunk_size):
                chunk = member_mentions[i : i + chunk_size]
                field_name = f"Members ({i + 1}-{min(i + chunk_size, len(member_mentions))})"
                embed.add_field(
                    name=field_name,
                    value="\n".join(chunk),
                    inline=False,
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @role_group.command(
        name="user",
        description="List all club roles assigned to a specific user.",
    )
    @hr_only()
    @app_commands.describe(
        user="Member whose roles to view",
    )
    async def role_user(
        interaction: discord.Interaction,
        user: discord.Member,
    ) -> None:
        service = _get_role_service(interaction.client)  # type: ignore[arg-type]
        roles = service.get_member_roles(user.id)

        if not roles:
            await interaction.response.send_message(
                f"{user.mention} has no assigned club roles.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"Club Roles for {user.display_name}",
            description=f"Total: {len(roles)} role(s)",
            color=discord.Color.blurple(),
        )

        for role in roles:
            value = f"ID: `{role.id}`"
            if role.description:
                value += f"\n{role.description}"
            embed.add_field(
                name=role.name,
                value=value,
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    tree.add_command(role_group)

