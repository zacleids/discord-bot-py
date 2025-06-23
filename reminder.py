from datetime import datetime

import discord

from log import get_ray_id, log_event
from models import Reminder


class EditReminderModal(discord.ui.Modal, title="Edit Reminder"):
    def __init__(self, reminder_id: int, existing_message: str, remind_at: datetime):
        super().__init__()
        self.reminder_id = reminder_id

        # Prefill the text field with the existing message
        self.message_input = discord.ui.TextInput(label="Edit message", default=existing_message, style=discord.TextStyle.short)
        self.add_item(self.message_input)

        # Prefill the datetime field with the existing remind_at time
        self.remind_at_input = discord.ui.TextInput(
            label="Edit remind at (YYYY-MM-DD HH:MM:SS)", default=remind_at.strftime("%Y-%m-%d %H:%M:%S"), style=discord.TextStyle.short
        )
        self.add_item(self.remind_at_input)

    async def on_submit(self, interaction: discord.Interaction):
        new_message = self.message_input.value
        new_remind_at = datetime.strptime(self.remind_at_input.value, "%Y-%m-%d %H:%M:%S")

        reminder_instance = Reminder.get_by_id(self.reminder_id)
        # AUDIT LOG: Log before/after edit
        log_event(
            "AUDIT_LOG",
            {
                "event": "AUDIT_LOG",
                "action": "reminder_edit",
                "user_id": interaction.user.id,
                "reminder_id": reminder_instance.id,
                "before": {"message": reminder_instance.message, "remind_at": str(reminder_instance.remind_at)},
                "after": {"message": new_message, "remind_at": str(new_remind_at)},
                "ray_id": get_ray_id(),
            },
            level="info",
        )
        reminder_instance.message = new_message
        reminder_instance.remind_at = new_remind_at
        reminder_instance.save()

        await interaction.response.send_message("Reminder updated successfully!", ephemeral=True)
