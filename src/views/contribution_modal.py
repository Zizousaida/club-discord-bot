from __future__ import annotations

from typing import Optional

import discord

from services.contribution_service import ContributionService


class ContributionModal(discord.ui.Modal, title="Submit Contribution"):
    """
    Modal presented to members when they run /contribute.

    Collects a required description of their work and optional links.
    """

    description: discord.ui.TextInput
    links: discord.ui.TextInput

    def __init__(self, service: ContributionService, user: discord.User) -> None:
        super().__init__(timeout=300)

        self.service = service
        self.user = user

        self.description = discord.ui.TextInput(
            label="What did you work on?",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=2000,
            placeholder="Describe your contribution in detail...",
        )
        self.links = discord.ui.TextInput(
            label="Links (GitHub, docs, etc.)",
            style=discord.TextStyle.short,
            required=False,
            max_length=500,
            placeholder="Optional links to your work",
        )

        self.add_item(self.description)
        self.add_item(self.links)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """
        When the user submits the modal, create a contribution entry
        and acknowledge privately.
        """
        links_value: Optional[str] = str(self.links.value).strip() or None

        # Store contribution through the service layer
        self.service.submit_contribution(
            user_id=self.user.id,
            username=str(self.user),
            description=str(self.description.value).strip(),
            links=links_value,
        )

        await interaction.response.send_message(
            "✅ Thank you! Your contribution has been recorded and will be reviewed by HR.",
            ephemeral=True,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        # Basic user-friendly error handling; errors should also be logged by the bot.
        await interaction.response.send_message(
            "⚠️ Something went wrong while saving your contribution. Please try again later.",
            ephemeral=True,
        )


