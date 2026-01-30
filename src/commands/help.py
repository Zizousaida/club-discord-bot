from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

import config


def _has_named_role(member: discord.Member, role_name: str) -> bool:
    """Return True if the given member has a role with the provided name."""
    if not isinstance(member, discord.Member):
        return False
    return any(role.name == role_name for role in member.roles)


def _is_hr(member: discord.Member) -> bool:
    """Check if a member has the HR role."""
    return _has_named_role(member, config.HR_ROLE_NAME)


def _is_staff(member: discord.Member) -> bool:
    """Check if a member has the Staff or HR role."""
    return _has_named_role(member, config.STAFF_ROLE_NAME) or _has_named_role(member, config.HR_ROLE_NAME)


def setup_help_command(bot: commands.Bot) -> None:
    """
    Register the /help command that displays all available commands
    organized by categories.
    """

    tree = bot.tree

    @app_commands.command(
        name="help",
        description="View all available bot commands organized by category.",
    )
    async def help_cmd(interaction: discord.Interaction) -> None:
        """
        Display a comprehensive help menu showing all bot commands,
        organized by category and filtered by user permissions.
        """
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        is_hr = _is_hr(interaction.user)
        is_staff = _is_staff(interaction.user)

        embed = discord.Embed(
            title="🤖 Club Discord Bot - Command Help",
            description="All available commands organized by category.",
            color=discord.Color.blurple(),
        )

        # Member Commands (Everyone)
        member_commands = "**`/contribute`**\n"
        member_commands += "Submit a contribution to the HR team via a private modal.\n"
        member_commands += "• Opens a form with description and optional links\n"
        member_commands += "• All members can use this command\n\n"

        embed.add_field(
            name="📝 Member Commands",
            value=member_commands,
            inline=False,
        )

        # HR Commands
        if is_hr:
            hr_commands = "**`/contributions list [member] [limit]`**\n"
            hr_commands += "View all contributions or filter by a specific member.\n\n"

            hr_commands += "**`/contributions latest [limit]`**\n"
            hr_commands += "View the latest contributions submitted.\n\n"

            hr_commands += "**`/contributions approve <contribution_id>`**\n"
            hr_commands += "Approve a contribution by its ID.\n\n"

            hr_commands += "**`/contributions reject <contribution_id>`**\n"
            hr_commands += "Reject a contribution by its ID.\n\n"

            hr_commands += "**`/role create <name> [description]`**\n"
            hr_commands += "Create a new club organizational role.\n\n"

            hr_commands += "**`/role delete <name>`**\n"
            hr_commands += "Delete a club role (removes all member assignments).\n\n"

            hr_commands += "**`/role assign <user> <role>`**\n"
            hr_commands += "Assign a club role to a member.\n\n"

            hr_commands += "**`/role remove <user> <role>`**\n"
            hr_commands += "Remove a club role from a member.\n\n"

            hr_commands += "**`/role list`**\n"
            hr_commands += "List all club organizational roles.\n\n"

            hr_commands += "**`/role members <role>`**\n"
            hr_commands += "List all members with a specific role.\n\n"

            hr_commands += "**`/role user <user>`**\n"
            hr_commands += "View all roles assigned to a specific user.\n\n"

            embed.add_field(
                name="👔 HR Commands",
                value=hr_commands,
                inline=False,
            )

        # Staff Commands (Staff and HR)
        if is_staff:
            staff_commands = "**`/mute <member> <duration_minutes> [reason]`**\n"
            staff_commands += "Temporarily timeout a member (1-10080 minutes).\n\n"

            staff_commands += "**`/unmute <member> [reason]`**\n"
            staff_commands += "Remove timeout from a member.\n\n"

            staff_commands += "**`/warn <member> <reason>`**\n"
            staff_commands += "Issue a warning to a member.\n\n"

            staff_commands += "**`/warnings <member>`**\n"
            staff_commands += "View all warnings for a specific member.\n\n"

            staff_commands += "**`/clear <amount>`**\n"
            staff_commands += "Bulk delete recent messages (1-100) from the current channel.\n\n"

            embed.add_field(
                name="🛡️ Moderation Commands",
                value=staff_commands,
                inline=False,
            )

            # Announcement Commands
            announcement_commands = "**`/announce <channel> <announcement_type> <message> [ping_everyone]`**\n"
            announcement_commands += "Send an announcement to a specific channel.\n"
            announcement_commands += "• Types: General, Event, Important, Update, Reminder, Welcome\n"
            announcement_commands += "• Optional: Ping @everyone (requires permission)\n\n"

            embed.add_field(
                name="📢 Announcement Commands",
                value=announcement_commands,
                inline=False,
            )

        # Permission Notice
        if not is_hr and not is_staff:
            embed.add_field(
                name="ℹ️ Note",
                value="Some commands are restricted to HR and Staff roles. "
                "Contact a staff member if you need assistance.",
                inline=False,
            )

        embed.set_footer(
            text="Use slash commands (/) to access these commands in Discord."
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    try:
        tree.add_command(help_cmd)
    except Exception as e:
        # Log error if command registration fails
        import logging
        log = logging.getLogger(__name__)
        log.error(f"Failed to register /help command: {e}")
        raise

