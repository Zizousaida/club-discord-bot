from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from utils.permissions import staff_only


def _get_announcement_embed(
    announcement_type: str,
    message: str,
    author: discord.Member,
) -> discord.Embed:
    """Create an embed based on the announcement type."""
    
    # Define colors and emojis for each type
    type_configs = {
        "general": {
            "color": discord.Color.blue(),
            "emoji": "📢",
            "title": "General Announcement",
        },
        "event": {
            "color": discord.Color.green(),
            "emoji": "🎉",
            "title": "Event Announcement",
        },
        "important": {
            "color": discord.Color.red(),
            "emoji": "⚠️",
            "title": "Important Announcement",
        },
        "update": {
            "color": discord.Color.orange(),
            "emoji": "🔄",
            "title": "Update Announcement",
        },
        "reminder": {
            "color": discord.Color.gold(),
            "emoji": "⏰",
            "title": "Reminder",
        },
        "welcome": {
            "color": discord.Color.blurple(),
            "emoji": "👋",
            "title": "Welcome Announcement",
        },
    }
    
    config = type_configs.get(announcement_type.lower(), type_configs["general"])
    
    embed = discord.Embed(
        title=f"{config['emoji']} {config['title']}",
        description=message,
        color=config["color"],
        timestamp=discord.utils.utcnow(),
    )
    
    embed.set_footer(
        text=f"Announced by {author.display_name}",
        icon_url=author.display_avatar.url if author.display_avatar else None,
    )
    
    return embed


def setup_announcement_commands(bot: commands.Bot) -> None:
    """
    Register announcement-related slash commands on the bot's app command tree.
    
    Commands:
    - /announce: Send an announcement to a specific channel
    """
    
    tree = bot.tree
    
    @app_commands.command(
        name="announce",
        description="Send an announcement to a specific channel.",
    )
    @staff_only()
    @app_commands.describe(
        channel="The channel where the announcement will be sent",
        announcement_type="Type of announcement",
        message="The announcement message (paragraph) to send",
        ping_everyone="Whether to ping @everyone (default: False)",
    )
    @app_commands.choices(
        announcement_type=[
            app_commands.Choice(name="General", value="general"),
            app_commands.Choice(name="Event", value="event"),
            app_commands.Choice(name="Important", value="important"),
            app_commands.Choice(name="Update", value="update"),
            app_commands.Choice(name="Reminder", value="reminder"),
            app_commands.Choice(name="Welcome", value="welcome"),
        ]
    )
    async def announce(
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        announcement_type: str,
        message: str,
        ping_everyone: bool = False,
    ) -> None:
        """Send an announcement to the specified channel."""
        
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return
        
        # Check if bot has permission to send messages in the channel
        if not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message(
                f"❌ I do not have permission to send messages in {channel.mention}.",
                ephemeral=True,
            )
            return
        
        # Check if user wants to ping everyone and if they have permission
        if ping_everyone and not channel.permissions_for(interaction.user).mention_everyone:
            await interaction.response.send_message(
                "❌ You do not have permission to mention @everyone. The announcement will be sent without pinging.",
                ephemeral=True,
            )
            ping_everyone = False
        
        # Validate message length
        if len(message) > 2000:
            await interaction.response.send_message(
                "❌ The announcement message is too long. Maximum length is 2000 characters.",
                ephemeral=True,
            )
            return
        
        # Create the embed
        embed = _get_announcement_embed(
            announcement_type=announcement_type,
            message=message,
            author=interaction.user,
        )
        
        # Prepare the content (ping if requested)
        content = "@everyone" if ping_everyone else None
        
        try:
            # Send the announcement
            await channel.send(content=content, embed=embed)
            
            # Confirm to the user
            await interaction.response.send_message(
                f"✅ Announcement sent to {channel.mention}!",
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                f"❌ I do not have permission to send messages in {channel.mention}.",
                ephemeral=True,
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"❌ Failed to send announcement: {str(e)}",
                ephemeral=True,
            )
    
    tree.add_command(announce)

