from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

import config
from services.role_service import RoleService
from utils.permissions import hr_only


def _split_field_value(value: str, max_length: int = 1024) -> list[str]:
    """
    Split a field value into chunks that fit within Discord's embed field limit.

    Discord embed field values have a maximum length of 1024 characters.
    This function splits long values into multiple chunks, trying to break
    at newline boundaries when possible.
    """
    if len(value) <= max_length:
        return [value]

    chunks: list[str] = []
    lines = value.split("\n")
    current_chunk: list[str] = []
    current_length = 0

    for line in lines:
        line_length = len(line) + 1  # +1 for the newline character

        # If adding this line would exceed the limit
        if current_length + line_length > max_length:
            # If current chunk has content, save it
            if current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_length = 0

            # If a single line is too long, truncate it
            if len(line) > max_length:
                # Try to truncate at word boundaries if possible
                truncated = line[: max_length - 3] + "..."
                chunks.append(truncated)
            else:
                current_chunk.append(line)
                current_length = line_length
        else:
            current_chunk.append(line)
            current_length += line_length

    # Add any remaining content
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def _get_role_service(bot: commands.Bot) -> RoleService:
    """Get the RoleService instance from the bot."""
    service = getattr(bot, "role_service", None)
    if not isinstance(service, RoleService):
        raise RuntimeError("RoleService is not attached to the bot.")
    return service


async def _autocomplete_role_name(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    service = _get_role_service(interaction.client)  # type: ignore[arg-type]
    roles = service.list_all_roles()
    current_lower = (current or "").lower()
    matches = [r.name for r in roles if current_lower in r.name.lower()]
    return [app_commands.Choice(name=name, value=name) for name in matches[:25]]


async def _autocomplete_department_name(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    service = _get_role_service(interaction.client)  # type: ignore[arg-type]
    depts = service.list_all_departments()
    current_lower = (current or "").lower()
    matches = [d.name for d in depts if current_lower in d.name.lower()]
    return [app_commands.Choice(name=name, value=name) for name in matches[:25]]


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
        description: str | None = None,
    ) -> None:
        service = _get_role_service(interaction.client)  # type: ignore[arg-type]

        # Check if role already exists
        existing = service.get_role_by_name(name)
        if existing:
            await interaction.response.send_message(
                f"❌ A role named `{name}` already exists.",
                ephemeral=not config.COMMAND_RESPONSES_PUBLIC,
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
            await interaction.response.send_message(
                embed=embed, ephemeral=not config.COMMAND_RESPONSES_PUBLIC
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to create role: {str(e)}",
                ephemeral=not config.COMMAND_RESPONSES_PUBLIC,
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
                ephemeral=not config.COMMAND_RESPONSES_PUBLIC,
            )
            return

        assert role.id is not None
        deleted = service.delete_role(role.id)
        if deleted:
            await interaction.response.send_message(
                f"✅ Role `{name}` has been deleted. All member assignments have been removed.",
                ephemeral=not config.COMMAND_RESPONSES_PUBLIC,
            )
        else:
            await interaction.response.send_message(
                f"❌ Failed to delete role `{name}`.",
                ephemeral=not config.COMMAND_RESPONSES_PUBLIC,
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
        assert club_role.id is not None

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

    @role_assign.autocomplete("role")
    async def role_assign_role_autocomplete(
        interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return await _autocomplete_role_name(interaction, current)

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
        assert club_role.id is not None

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

    @role_remove.autocomplete("role")
    async def role_remove_role_autocomplete(
        interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return await _autocomplete_role_name(interaction, current)

    @role_group.command(
        name="list",
        description="List all club organizational roles grouped by department.",
    )
    @hr_only()
    async def role_list(
        interaction: discord.Interaction,
    ) -> None:
        service = _get_role_service(interaction.client)  # type: ignore[arg-type]

        # Get roles grouped by department
        roles_by_dept = service.get_roles_grouped_by_department()
        roles_without_dept = service.get_roles_without_department()

        if not roles_by_dept and not roles_without_dept:
            await interaction.response.send_message(
                "No club roles have been created yet.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="Club Organizational Roles",
            description="Roles grouped by department",
            color=discord.Color.blurple(),
        )

        # Add roles grouped by department
        for department, roles in roles_by_dept.items():
            role_list = []
            for role in roles:
                assert role.id is not None
                members = service.get_role_members(role.id)
                member_count = len(members)
                role_info = f"• **{role.name}** (ID: `{role.id}`) • {member_count} member(s)"
                if role.description:
                    # Truncate description if it's too long to prevent field overflow
                    desc = role.description
                    if len(desc) > 200:  # Leave room for other text in the role_info
                        desc = desc[:197] + "..."
                    role_info += f"\n  └ {desc}"
                role_list.append(role_info)

            dept_name = f"🏢 {department.name}"
            if department.description:
                dept_name += f" - {department.description}"

            field_value = "\n".join(role_list) if role_list else "No roles"
            # Split into multiple fields if value is too long
            value_chunks = _split_field_value(field_value)

            for i, chunk in enumerate(value_chunks):
                field_name = dept_name if i == 0 else f"{dept_name} (cont.)"
                embed.add_field(
                    name=field_name,
                    value=chunk,
                    inline=False,
                )

        # Add roles without department
        if roles_without_dept:
            role_list = []
            for role in roles_without_dept:
                assert role.id is not None
                members = service.get_role_members(role.id)
                member_count = len(members)
                role_info = f"• **{role.name}** (ID: `{role.id}`) • {member_count} member(s)"
                if role.description:
                    # Truncate description if it's too long to prevent field overflow
                    desc = role.description
                    if len(desc) > 200:  # Leave room for other text in the role_info
                        desc = desc[:197] + "..."
                    role_info += f"\n  └ {desc}"
                role_list.append(role_info)

            field_value = "\n".join(role_list)
            # Split into multiple fields if value is too long
            value_chunks = _split_field_value(field_value)

            for i, chunk in enumerate(value_chunks):
                field_name = "📋 Unassigned Roles" if i == 0 else "📋 Unassigned Roles (cont.)"
                embed.add_field(
                    name=field_name,
                    value=chunk,
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
        assert club_role.id is not None

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
        field_value = "\n".join(member_mentions) if member_mentions else "None"

        # Split into multiple fields if value is too long (1024 char limit)
        value_chunks = _split_field_value(field_value)

        for i, chunk in enumerate(value_chunks):
            if len(value_chunks) == 1:
                field_name = "Members"
            else:
                field_name = f"Members (part {i + 1})"

            embed.add_field(
                name=field_name,
                value=chunk,
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @role_members.autocomplete("role")
    async def role_members_role_autocomplete(
        interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return await _autocomplete_role_name(interaction, current)

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
                # Truncate description if it's too long (field value limit is 1024)
                desc = role.description
                max_desc_length = 1024 - len(value) - 1  # -1 for newline
                if len(desc) > max_desc_length:
                    desc = desc[: max_desc_length - 3] + "..."
                value += f"\n{desc}"
            # Ensure the entire value doesn't exceed 1024 characters
            if len(value) > 1024:
                value = value[:1021] + "..."
            embed.add_field(
                name=role.name,
                value=value,
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Department subcommands
    department_group = app_commands.Group(
        name="department",
        description="Manage departments for grouping roles.",
        parent=role_group,
    )

    @department_group.command(
        name="create",
        description="Create a new department.",
    )
    @hr_only()
    @app_commands.describe(
        name="Name of the department (must be unique)",
        description="Optional description of the department",
    )
    async def department_create(
        interaction: discord.Interaction,
        name: str,
        description: str | None = None,
    ) -> None:
        service = _get_role_service(interaction.client)  # type: ignore[arg-type]

        # Check if department already exists
        existing = service.get_department_by_name(name)
        if existing:
            await interaction.response.send_message(
                f"❌ A department named `{name}` already exists.",
                ephemeral=True,
            )
            return

        try:
            department = service.create_department(name=name, description=description)
            embed = discord.Embed(
                title="✅ Department Created",
                description=f"Created department `{department.name}` (ID: {department.id})",
                color=discord.Color.green(),
            )
            if department.description:
                embed.add_field(name="Description", value=department.description, inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to create department: {str(e)}",
                ephemeral=True,
            )

    @department_group.command(
        name="assign",
        description="Assign roles to a department by their IDs.",
    )
    @hr_only()
    @app_commands.describe(
        department="Name of the department",
        role_ids="Comma-separated list of role IDs to assign (e.g., 1,2,3)",
    )
    async def department_assign(
        interaction: discord.Interaction,
        department: str,
        role_ids: str,
    ) -> None:
        service = _get_role_service(interaction.client)  # type: ignore[arg-type]

        dept = service.get_department_by_name(department)
        if not dept:
            await interaction.response.send_message(
                f"❌ Department `{department}` not found.",
                ephemeral=True,
            )
            return
        assert dept.id is not None

        # Parse role IDs
        try:
            role_id_list = [int(rid.strip()) for rid in role_ids.split(",")]
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid role IDs format. Please provide comma-separated numbers (e.g., 1,2,3).",
                ephemeral=True,
            )
            return

        if not role_id_list:
            await interaction.response.send_message(
                "❌ No role IDs provided.",
                ephemeral=True,
            )
            return

        # Validate and assign roles
        assigned = []
        not_found = []
        already_assigned = []

        for role_id in role_id_list:
            role = service.get_role_by_id(role_id)
            if not role:
                not_found.append(str(role_id))
                continue

            # Check if already assigned
            dept_roles = service.get_roles_for_department(dept.id)
            if role in dept_roles:
                already_assigned.append(role.name)
                continue

            if service.assign_role_to_department(
                department_id=dept.id,
                role_id=role_id,
            ):
                assigned.append(role.name)
            else:
                already_assigned.append(role.name)

        # Build response
        embed = discord.Embed(
            title="📋 Role Assignment Results",
            color=discord.Color.blurple(),
        )

        if assigned:
            embed.add_field(
                name="✅ Assigned",
                value="\n".join(f"• {name}" for name in assigned),
                inline=False,
            )

        if already_assigned:
            embed.add_field(
                name="⚠️ Already Assigned",
                value="\n".join(f"• {name}" for name in already_assigned),
                inline=False,
            )

        if not_found:
            embed.add_field(
                name="❌ Not Found",
                value="\n".join(f"• ID: {rid}" for rid in not_found),
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @department_assign.autocomplete("department")
    async def department_assign_dept_autocomplete(
        interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return await _autocomplete_department_name(interaction, current)

    @department_group.command(
        name="remove",
        description="Remove roles from a department by their IDs.",
    )
    @hr_only()
    @app_commands.describe(
        department="Name of the department",
        role_ids="Comma-separated list of role IDs to remove (e.g., 1,2,3)",
    )
    async def department_remove(
        interaction: discord.Interaction,
        department: str,
        role_ids: str,
    ) -> None:
        service = _get_role_service(interaction.client)  # type: ignore[arg-type]

        dept = service.get_department_by_name(department)
        if not dept:
            await interaction.response.send_message(
                f"❌ Department `{department}` not found.",
                ephemeral=True,
            )
            return
        assert dept.id is not None

        # Parse role IDs
        try:
            role_id_list = [int(rid.strip()) for rid in role_ids.split(",")]
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid role IDs format. Please provide comma-separated numbers (e.g., 1,2,3).",
                ephemeral=True,
            )
            return

        if not role_id_list:
            await interaction.response.send_message(
                "❌ No role IDs provided.",
                ephemeral=True,
            )
            return

        # Remove roles
        removed = []
        not_found = []
        not_assigned = []

        for role_id in role_id_list:
            role = service.get_role_by_id(role_id)
            if not role:
                not_found.append(str(role_id))
                continue

            if service.remove_role_from_department(
                department_id=dept.id,
                role_id=role_id,
            ):
                removed.append(role.name)
            else:
                not_assigned.append(role.name)

        # Build response
        embed = discord.Embed(
            title="📋 Role Removal Results",
            color=discord.Color.orange(),
        )

        if removed:
            embed.add_field(
                name="✅ Removed",
                value="\n".join(f"• {name}" for name in removed),
                inline=False,
            )

        if not_assigned:
            embed.add_field(
                name="⚠️ Not Assigned",
                value="\n".join(f"• {name}" for name in not_assigned),
                inline=False,
            )

        if not_found:
            embed.add_field(
                name="❌ Not Found",
                value="\n".join(f"• ID: {rid}" for rid in not_found),
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @department_remove.autocomplete("department")
    async def department_remove_dept_autocomplete(
        interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return await _autocomplete_department_name(interaction, current)

    @department_group.command(
        name="list",
        description="List all departments and their roles.",
    )
    @hr_only()
    async def department_list(
        interaction: discord.Interaction,
    ) -> None:
        service = _get_role_service(interaction.client)  # type: ignore[arg-type]
        departments = service.list_all_departments()

        if not departments:
            await interaction.response.send_message(
                "No departments have been created yet.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="Departments",
            color=discord.Color.blurple(),
        )

        for dept in departments:
            assert dept.id is not None
            roles = service.get_roles_for_department(dept.id)
            dept_name = f"🏢 {dept.name}"
            if dept.description:
                dept_name += f" - {dept.description}"

            if roles:
                role_list = [f"• {role.name} (ID: `{role.id}`)" for role in roles]
                value = f"**{len(roles)} role(s):**\n" + "\n".join(role_list)
            else:
                value = "No roles assigned"

            # Split into multiple fields if value is too long
            value_chunks = _split_field_value(value)

            for i, chunk in enumerate(value_chunks):
                field_name = dept_name if i == 0 else f"{dept_name} (cont.)"
                embed.add_field(
                    name=field_name,
                    value=chunk,
                    inline=False,
                )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @department_group.command(
        name="delete",
        description="Delete a department.",
    )
    @hr_only()
    @app_commands.describe(
        name="Name of the department to delete",
    )
    async def department_delete(
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        service = _get_role_service(interaction.client)  # type: ignore[arg-type]

        dept = service.get_department_by_name(name)
        if not dept:
            await interaction.response.send_message(
                f"❌ Department `{name}` not found.",
                ephemeral=True,
            )
            return

        assert dept.id is not None
        deleted = service.delete_department(dept.id)
        if deleted:
            await interaction.response.send_message(
                f"✅ Department `{name}` has been deleted. All role assignments have been removed.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ Failed to delete department `{name}`.",
                ephemeral=True,
            )

    @department_delete.autocomplete("name")
    async def department_delete_dept_autocomplete(
        interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return await _autocomplete_department_name(interaction, current)

    tree.add_command(role_group)
