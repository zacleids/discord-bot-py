from datetime import datetime
from models import orm_db, Reminder
import discord

class EditReminderModal(discord.ui.Modal, title="Edit Reminder"):
    def __init__(self, reminder_id: int, existing_message: str, remind_at: datetime):
        super().__init__()
        self.reminder_id = reminder_id

        # Prefill the text field with the existing message
        self.message_input = discord.ui.TextInput(
            label="Edit message",
            default=existing_message,
            style=discord.TextStyle.short
        )
        self.add_item(self.message_input)

        # Prefill the datetime field with the existing remind_at time
        self.remind_at_input = discord.ui.TextInput(
            label="Edit remind at (YYYY-MM-DD HH:MM:SS)",
            default=remind_at.strftime("%Y-%m-%d %H:%M:%S"),
            style=discord.TextStyle.short
        )
        self.add_item(self.remind_at_input)

    async def on_submit(self, interaction: discord.Interaction):
        new_message = self.message_input.value
        new_remind_at = datetime.strptime(self.remind_at_input.value, "%Y-%m-%d %H:%M:%S")

        reminder_instance = Reminder.get_by_id(self.reminder_id)
        reminder_instance.message = new_message
        reminder_instance.remind_at = new_remind_at
        reminder_instance.save()

        await interaction.response.send_message(f"Reminder updated successfully!", ephemeral=True)
