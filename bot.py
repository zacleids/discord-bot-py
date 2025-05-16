import asyncio
from datetime import datetime, timedelta, timezone

import emoji
import os
import random
import re

import discord
import discord.ext
from discord.ext import tasks
import pytz
from dotenv import load_dotenv

import coin
import color
import db.db
import dice
import eight_ball
import encode
import hangman
import rps
import time_funcs
import todo
import text_transform
import daily_checklist
import fortune
import conversion
import currency
from errors import InvalidInputError
from log_interaction import log_interaction
from reminder import Reminder, EditReminderModal
from config import Config
from utils import format_number, guild_only

# Initialize config
config = Config()

# Create bot instance
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Ensure message content is explicitly enabled
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

#  https://stackoverflow.com/questions/77958066/how-do-i-add-subcommand-support-with-discord-py
todo_command_group = discord.app_commands.Group(name="todo", description="Manage your todo list")
tree.add_command(todo_command_group)

clock_command_group = discord.app_commands.Group(name="clock", description="Manage your world clock")
tree.add_command(clock_command_group)

hangman_command_group = discord.app_commands.Group(name="hangman", description="Play hangman")
tree.add_command(hangman_command_group)

reminder_command_group = discord.app_commands.Group(name="reminder", description="Set a reminder")
tree.add_command(reminder_command_group)

daily_command_group = discord.app_commands.Group(name="daily", description="Manage your daily checklist")
tree.add_command(daily_command_group)

# Ensure the database and tasks table are set up
db.db.create_dbs()


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    check_reminders.start()


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return  # Ignore the bot's own messages

    message_content = message.content

    if not message_content.startswith(config.command_prefix):
        return  # Ignore message that don't start with the command prefix

    # Support logging for both DMs and guild messages
    if message.guild is not None:
        log_str = f"! command \t\t| Server: {message.guild.name}, Channel: {message.channel.name}, Author: {message.author}, Content: {message.content}"
    else:
        log_str = f"! command \t\t| DM from: {message.author}, Content: {message.content}"
    print(log_str)

    command_body = message_content[len(config.command_prefix):].split(" ")
    command = command_body[0].lower()
    args = command_body[1:]

    try:
        result = "Uh Oh, something went wrong"
        files = None
        match command:
            case "sync":
                if message.author.id == config.bot_admin_id:
                    await message.channel.send("Syncing commands...")
                    info = await tree.sync()
                    result = "Commands synced!"

                    #Send the sync info directly to the admin user
                    cmd_names = set()
                    for cmd in info:
                        added = False
                        for option in cmd.options:
                            if option.type.name == discord.AppCommandOptionType.subcommand.name:
                                cmd_names.add(f"{cmd.name} {option.name}")
                                added = True
                        if not added:
                            cmd_names.add(cmd.name)

                    cmd_names = sorted(cmd_names)
                    info_message = f"Sync completed. {len(info)} top level commands registered & {len(cmd_names)} total commands registered:\n" + "\n".join(cmd_names)
                    await message.author.send(info_message)
                else:
                    result = "You don't have permission to sync commands."
            case "hello" | "hi" | "hey":
                await message.add_reaction("👋")
                result = "Hello!"
            case "f":
                result = await eight_ball.f_in_chat(message)
            case "gg":
                result = eight_ball.gg()
            case "coinflip" | "coin" | "flip" | "coin_flip":
                result = coin.flip_coin()
            case "coinflip_n" | "coin_n" | "flip_n" | "coin_flip_n":
                result = coin.flip_coins(args)
            case "eight" | "eightball" | "8ball":
                result = await eight_ball.eight_ball(args, message)
            case "r" | "roll" | "dice" | "roll_dice":
                result = dice.dice_roll_command(args)
            case "rps" | "rock" | "paper" | "scissors":
                result = rps.play_rock_paper_scissors(args)
            case "todo":
                result = todo.handle_todo_command(args, message.author, message.mentions)
            case "color":
                result, files = color.handle_color_command(args)
            case "clock" | "clocks":
                # Only use message.guild.id if in a guild, else use the user ID
                # This is to support DMs
                guild_id = message.guild.id if message.guild else message.author.id
                result = time_funcs.handle_world_clock_command(args, guild_id)
            case "encode":
                result = encode.handle_encode_decode_command(args, "encode")
            case "decode":
                result = encode.handle_encode_decode_command(args, "decode")
            case "transform":
                result = text_transform.handle_text_transform_command(args)
            case "daily":
                result = daily_checklist.handle_daily_checklist_command(args, message.author)
            case "fortune":
                result = fortune.get_fortune(message.author.id)
            case "conversion":
                result = conversion.handle_conversion_command(args)
            case "currency":
                result = currency.handle_currency_command(args)
            case "rand" | "random":
                result = dice.random_command(args)
            case _:
                result = "Command not recognized."
        if files:
            await message.channel.send(result, files=[discord.File(file) for file in files])
        else:
            await message.channel.send(result)

    except InvalidInputError as e:
        await message.channel.send(f"Error: {e}")
    except ValueError as e:
        await message.channel.send(f"Error: {e}")


#  https://gist.github.com/Rapptz/c4324f17a80c94776832430007ad40e6
#  https://fallendeity.github.io/discord.py-masterclass/slash-commands/#slash-command-parameters
@tree.command(name="f", description="f in the chat")
@log_interaction
async def f_slash_command(interaction: discord.Interaction):
    result = await eight_ball.f_in_chat()
    await interaction.response.send_message(result)


@tree.command(name="gg", description="Good Game!")
@log_interaction
async def gg_slash_command(interaction: discord.Interaction):
    result = eight_ball.gg()
    await interaction.response.send_message(result)


@tree.command(name="coinflip", description="flip a coin")
@log_interaction
async def coinflip_slash_command(interaction: discord.Interaction):
    result = coin.flip_coin()
    await interaction.response.send_message(result)


@tree.command(name="coinflip_n", description="flip N number of coins")
@log_interaction
async def coinflip_n_slash_command(interaction: discord.Interaction, number: discord.app_commands.Range[int, 1, 100000]):
    result = coin.flip_coins([str(number)])
    await interaction.response.send_message(result)


@tree.command(name="eightball", description="ask the magic eightball")
@log_interaction
async def eightball_slash_command(interaction: discord.Interaction, message: str):
    result = await eight_ball.eight_ball(message.split(" "))
    await interaction.response.send_message(result)


@tree.command(name="roll", description=r"roll some dice {num}d{num} ie. \`1d20\`")
@log_interaction
async def roll_slash_command(interaction: discord.Interaction, dice_roll: str):
    result = dice.dice_roll_command(dice_roll.split(" "))
    await interaction.response.send_message(dice_roll + "\n" + result)


@tree.command(name="random", description="generate a random number")
@log_interaction
async def roll_slash_command(interaction: discord.Interaction, number1: float, number2: float):
    result = dice.random_command([str(number1),  str(number2)])
    await interaction.response.send_message(result)


@tree.command(name="rps", description="Play Rock, Paper, Scissors")
@log_interaction
async def rps_slash_command(interaction: discord.Interaction, player_choice: rps.RPSChoice):
    bot_choice = random.choice(list(rps.RPSChoice))
    result = rps.print_win_str(bot_choice, player_choice)
    await interaction.response.send_message(result)


@tree.command(name="encode", description="Encode a message")
@log_interaction
async def encode_slash_command(interaction: discord.Interaction, message: str, encoder: encode.EncoderChoice):
    # result = encode.encode_decode(message, encoder.value)
    args = [encoder.value] +  message.split(" ")
    result = encode.handle_encode_decode_command(args, "encode")
    await interaction.response.send_message(result)

@tree.command(name="decode", description="Decode a message")
@log_interaction
async def decode_slash_command(interaction: discord.Interaction, message: str, encoder: encode.EncoderChoiceWithoutAll):
    # result = encode.encode_decode(message, encoder.value, operation='decode')
    args = [encoder.value] +  message.split(" ")
    result = encode.handle_encode_decode_command(args, "decode")
    await interaction.response.send_message(result)


@tree.command(name="color", description="generate an image of a given color or random color if supplied with 'random'")
@log_interaction
async def color_slash_command(interaction: discord.Interaction, color_str: str = None, num_colors: discord.app_commands.Range[int, 1, 10] = 1, include_inverted: bool = False):
    if not color_str:
        color_str = ["random", str(num_colors)]
    elif color_str.lower() in ["random", "rand", "r"]:
        color_str = ["random", str(num_colors)]
    else:
        color_str = color_str.split(" ")
    if include_inverted:
        color_str.append("include_inverted:true")
    result, files = color.handle_color_command(color_str)
    await interaction.response.send_message(result, files=[discord.File(file) for file in files])


@tree.command(name="transform", description="Transform text in various ways")
@log_interaction
async def transform_slash_command(interaction: discord.Interaction, text: str, transform_type: text_transform.TransformChoice):
    result = text_transform.transform_text(text, transform_type)
    await interaction.response.send_message(result)


@tree.command(name="fortune", description="Get your fortune for today!")
@log_interaction
async def fortune_slash_command(interaction: discord.Interaction):
    result = fortune.get_fortune(interaction.user.id)
    await interaction.response.send_message(result)


@tree.command(name="conversion", description="Convert between units (length, mass, volume)")
@log_interaction
async def conversion_slash_command(
    interaction: discord.Interaction,
    from_unit: conversion.UnitTypeChoice,
    to_unit: conversion.UnitTypeChoice,
    number: float,
    height_display: bool = False
):
    try:
        from_enum = conversion.parse_unit(from_unit.value)
        to_enum = conversion.parse_unit(to_unit.value)
        result = conversion.get_conversion_display(from_enum, to_enum, number, height_display=height_display)
        await interaction.response.send_message(result)
    except ValueError as e:
        await interaction.response.send_message(str(e))


@tree.command(name="height", description="Convert between feet/inches and centimeters")
@log_interaction
async def height_slash_command(
    interaction: discord.Interaction,
    feet: int = None,
    inches: int = None,
    centimeters: float = None
):
    # If centimeters is provided, do not allow feet or inches
    if centimeters is not None:
        if feet is not None or inches is not None:
            await interaction.response.send_message("Please provide either centimeters OR feet/inches, not both.")
            return
        from_unit = conversion.UnitType.CENTIMETER
        to_unit = conversion.UnitType.FOOT
        result = conversion.get_conversion_display(from_unit, to_unit, centimeters, height_display=True)
        await interaction.response.send_message(result)
        return
    # Otherwise, convert feet/inches to centimeters
    if feet is not None or inches is not None:
        total_inches = feet * 12 + (inches or 0)
        from_unit = conversion.UnitType.INCH
        to_unit = conversion.UnitType.CENTIMETER
        result = conversion.get_conversion_display(from_unit, to_unit, total_inches, feet_inches_input=(feet, inches))
        await interaction.response.send_message(result)
        return
    await interaction.response.send_message("Please provide either centimeters or feet (and optionally inches) to convert.", ephemeral=True)


# Provide choices for the dropdowns using CURRENCY_NAMES, with contains search
async def currency_list_autocomplete(interaction: discord.Interaction, current: str):
    current_lower = current.lower()
    return [
        discord.app_commands.Choice(name=f"{code} - {currency.get_currency_name(code)}", value=code)
        for code in currency.CURRENCY_NAMES
        if current_lower in code.lower() or current_lower in currency.get_currency_name(code).lower()
    ][:25]

@tree.command(name="currency", description="Convert between currencies")
@discord.app_commands.autocomplete(
    from_currency=currency_list_autocomplete,
    to_currency=currency_list_autocomplete
    )
@log_interaction
async def currency_slash_command(
    interaction: discord.Interaction,
    from_currency: str,
    to_currency: str,
    amount: float
):
    try:
        result = currency.convert_currency(from_currency, to_currency, amount)
        await interaction.response.send_message(
            f"{format_number(amount)} {from_currency} = {format_number(result)} {to_currency}"
        )
    except Exception as e:
        await interaction.response.send_message(str(e), ephemeral=True)


# Subcommand `/todo add`
@todo_command_group.command(name="add", description="Add a task to your todo list")
@log_interaction
async def todo_add_slash_command(interaction: discord.Interaction, task: str, position: discord.app_commands.Range[int, 1, 100] = None,
              user: discord.User = None):
    user = user or interaction.user  # Default to the interaction user if no mention
    todo.add_task(user.id, task, position)  # Add the task to the database with the user ID
    result = f"Task added: {task}"
    await interaction.response.send_message(result)


# Subcommand `/todo list`
@todo_command_group.command(name="list", description="List all your tasks")
@log_interaction
async def todo_list_slash_command(interaction: discord.Interaction, user: discord.User = None):
    user = user or interaction.user  # Default to the interaction user if no mention
    tasks = todo.list_tasks(user.id)  # Get tasks for the user
    if tasks:
        response = todo.get_tasks_response_str(tasks)
        await interaction.response.send_message(response)
    else:
        await interaction.response.send_message("Your todo list is empty.")


# Subcommand `/todo remove`
@todo_command_group.command(name="remove", description="Remove a task from your todo list")
@log_interaction
async def todo_remove_slash_command(interaction: discord.Interaction, position: int, user: discord.User = None):
    user = user or interaction.user  # Default to the interaction user if no mention
    response = todo.remove_task(user.id, position)
    await interaction.response.send_message(response)


# Subcommand `/todo move`
@todo_command_group.command(name="move", description="Set the priority of a task")
@log_interaction
async def todo_move_slash_command(interaction: discord.Interaction, old_position: int, new_position: int, user: discord.User = None):
    user = user or interaction.user  # Default to the interaction user if no mention
    result = todo.move_task(user.id, old_position, new_position)
    await interaction.response.send_message(result)


# Subcommand `/todo edit`
@todo_command_group.command(name="edit", description="Edit a task")
@log_interaction
async def todo_edit_slash_command(interaction: discord.Interaction, position: int, user: discord.User = None):
    user = user or interaction.user  # Default to the interaction user if no mention
    user_id = user.id
    existing_task = todo.get_task(user_id, position)

    if existing_task is None:
        await interaction.response.send_message("Task not found.")
        return

    # Send the modal
    await interaction.response.send_modal(todo.EditTaskModal(user_id, position, existing_task))


# Subcommand `/clock list`
@clock_command_group.command(name="list", description="List all clocks in your world clock")
@log_interaction
async def clock_list_slash_command(interaction: discord.Interaction):
    # Use user.id for DMs, guild_id for servers
    key_id = interaction.guild_id if interaction.guild_id is not None else interaction.user.id
    tzs = time_funcs.list_timezones(key_id)
    if tzs:
        response = time_funcs.format_tzs_response_str(tzs)
        await interaction.response.send_message(response)
    else:
        await interaction.response.send_message("There are no clocks in your world clock")


async def clock_full_list_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    existing = [x.timezone_str for x in time_funcs.list_timezones(interaction.guild_id)]
    options = [tz for tz in pytz.all_timezones if tz not in existing]
    return [discord.app_commands.Choice(name=option, value=option) for option in options if option.lower().startswith(current.lower())][:25]


async def clock_existing_list_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    options = [x.timezone_str for x in time_funcs.list_timezones(interaction.guild_id)]
    return [discord.app_commands.Choice(name=option, value=option) for option in options if option.lower().startswith(current.lower())][:25]


# Subcommand `/clock add`
@clock_command_group.command(name="add", description="Add a clock to your world clock")
@discord.app_commands.autocomplete(timezone=clock_full_list_autocomplete)
@log_interaction
async def clock_add_slash_command(interaction: discord.Interaction, timezone: str, label: str = None):
    key_id = interaction.guild_id if interaction.guild_id is not None else interaction.user.id
    tz = time_funcs.get_valid_timezone(timezone)
    result = time_funcs.add_timezone(key_id, tz, label)
    await interaction.response.send_message(result)


# Subcommand `/clock remove`
@clock_command_group.command(name="remove", description="Remove a clock to your world clock")
@discord.app_commands.autocomplete(timezone=clock_existing_list_autocomplete)
@log_interaction
async def clock_remove_slash_command(interaction: discord.Interaction, timezone: str):
    key_id = interaction.guild_id if interaction.guild_id is not None else interaction.user.id
    result = time_funcs.remove_timezone(key_id, timezone)
    await interaction.response.send_message(result)


# Subcommand `/clock edit`
@clock_command_group.command(name="edit", description="Edit a clock label from your world clock")
@discord.app_commands.autocomplete(timezone=clock_existing_list_autocomplete)
@log_interaction
async def clock_edit_slash_command(interaction: discord.Interaction, timezone: str):
    key_id = interaction.guild_id if interaction.guild_id is not None else interaction.user.id
    existing_tz = time_funcs.get_timezone(key_id, timezone)

    if existing_tz is None:
        await interaction.response.send_message("Timezone not found.")
        return

    # Send the modal
    await interaction.response.send_modal(time_funcs.EditTimezoneLabelModal(key_id, timezone, existing_tz.label if existing_tz.label else ""))


# Subcommand `/hangman startgame`
@hangman_command_group.command(name="startgame", description="Start a game of hangman")
@guild_only
@log_interaction
async def hangman_startgame_slash_command(interaction: discord.Interaction, phrase: str, num_guesses: discord.app_commands.Range[int, 1, 26] = None):
    valid, error_msg = hangman.validate_chars(phrase)

    if not valid:
        await interaction.response.send_message(error_msg, ephemeral=True)
        return

    hg = hangman.get_active_hangman_game(interaction.guild_id)
    if hg is not None:
        await interaction.response.send_message("There is already an active hangman game.")
        return

    hg = hangman.HangmanGame.create(guild_id=interaction.guild_id, user_id=interaction.user.id, phrase=phrase, num_guesses=num_guesses)
    hg.calculate_board()
    response = hg.print_board()
    await interaction.response.send_message(response)


# Subcommand `/hangman display`
@hangman_command_group.command(name="display", description="Display the state of the current hangman game")
@guild_only
@log_interaction
async def hangman_display_slash_command(interaction: discord.Interaction):
    hg = hangman.get_active_hangman_game(interaction.guild_id)
    if hg is None:
        await interaction.response.send_message("No hangman game active.")
        return

    response = hg.print_board() + f"\nGame expires {discord.utils.format_dt(hg.created_at + timedelta(hours=8), style='R')}"

    await interaction.response.send_message(response)


# Subcommand `/hangman guess`
@hangman_command_group.command(name="guess", description="Guess some letters for the current hangman game")
@guild_only
@log_interaction
async def hangman_guess_slash_command(interaction: discord.Interaction, guess: str):
    valid, error_msg = hangman.validate_chars(guess)

    if not valid:
        await interaction.response.send_message(error_msg, ephemeral=True)
        return

    hg = hangman.get_active_hangman_game(interaction.guild_id)
    if hg is None:
        await interaction.response.send_message("No hangman game active.")
        return

    hg.guess_new_letters(guess)
    response = hg.print_board()
    await interaction.response.send_message(response)


async def reminder_existing_list_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    options = [x.message for x in Reminder.select().where(Reminder.user_id == interaction.user.id).order_by(Reminder.remind_at)]
    return [discord.app_commands.Choice(name=option, value=option) for option in options if option.lower().startswith(current.lower())][:25]


# Subcommand `/reminder add`
@reminder_command_group.command(name="add", description="Add a reminder")
@log_interaction
async def reminder_add_slash_command(interaction: discord.Interaction, message: str, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0,
                                     user: discord.User = None, is_private: bool = False):
    user = user or interaction.user  # Default to the interaction user if no mention
    remind_time = datetime.now() + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    guild_id = interaction.guild_id if interaction.guild_id is not None else user.id
    channel_id = interaction.channel_id if interaction.channel_id is not None else interaction.channel.id
    Reminder.create(user_id=user.id, guild_id=guild_id, channel_id=channel_id, message=message, remind_at=remind_time, is_private=is_private)

    if is_private:
        await interaction.response.send_message(f"Reminder set for {discord.utils.format_dt(remind_time, style='F')}! (Private reminder)", ephemeral=True) # only the creating user can see this
    else:
        await interaction.response.send_message(f"Reminder set for {discord.utils.format_dt(remind_time, style='F')}!")


# Subcommand `/reminder list`
@reminder_command_group.command(name="list", description="List all your reminders")
@log_interaction
async def reminder_list_slash_command(interaction: discord.Interaction, user: discord.User = None):
    user = user or interaction.user  # Default to the interaction user if no mention
    public_reminders = Reminder.select().where(Reminder.user_id == user.id, Reminder.is_private == False).order_by(Reminder.remind_at)
    private_reminders = Reminder.select().where(Reminder.user_id == user.id, Reminder.is_private == True).order_by(Reminder.remind_at)

    response = "**Your upcoming public reminders:**\n"
    if public_reminders:
        for r in public_reminders:
            channel = client.get_channel(r.channel_id)
            channel_mention = channel.mention if channel else "Unknown Channel"
            response += f"- `{r.message}` in {channel_mention} at {discord.utils.format_dt(r.remind_at, style='F')}\n"
    else:
        response += "You have no upcoming public reminders."

    await interaction.response.send_message(response)

    if private_reminders:
        private_response = "**Your upcoming private reminders:**\n"
        for r in private_reminders:
            private_response += f"- `{r.message}` at {discord.utils.format_dt(r.remind_at, style='F')}\n"
        await user.send(private_response)


# Subcommand `/reminder remove`
@reminder_command_group.command(name="remove", description="Remove a reminder from your reminder list")
@discord.app_commands.autocomplete(reminder=reminder_existing_list_autocomplete)
@log_interaction
async def reminder_remove_slash_command(interaction: discord.Interaction, reminder: str):
    user = interaction.user
    reminder_instance = Reminder.get_or_none(Reminder.user_id == user.id, Reminder.message == reminder)

    if reminder_instance:
        channel = client.get_channel(reminder_instance.channel_id)
        channel_mention = channel.mention if channel else "Unknown Channel"
        reminder_instance.delete_instance()
        response_message = f"Reminder `{reminder}` in {channel_mention} has been removed."
        await interaction.response.send_message(response_message, ephemeral=reminder_instance.is_private)
    else:
        await interaction.response.send_message(f"Reminder `{reminder}` not found.", ephemeral=True)


# Subcommand `/reminder edit`
@reminder_command_group.command(name="edit", description="Edit a reminder")
@discord.app_commands.autocomplete(reminder=reminder_existing_list_autocomplete)
@log_interaction
async def reminder_edit_slash_command(interaction: discord.Interaction, reminder: str):
    user = interaction.user
    reminder_instance = Reminder.get_or_none(Reminder.user_id == user.id, Reminder.message == reminder)

    if reminder_instance:
        await interaction.response.send_modal(EditReminderModal(reminder_instance.id, reminder_instance.message, reminder_instance.remind_at))
    else:
        await interaction.response.send_message(f"Reminder `{reminder}` not found.", ephemeral=True)


# Subcommand `/daily add`
@daily_command_group.command(name="add", description="Add an item to your daily checklist")
@log_interaction
async def daily_add_slash_command(interaction: discord.Interaction, item: str):
    daily_checklist.add_item(interaction.user.id, item)
    await interaction.response.send_message(f"Item added: {item}")


# Subcommand `/daily remove`
@daily_command_group.command(name="remove", description="Remove an item by its position")
@log_interaction
async def daily_remove_slash_command(interaction: discord.Interaction, position: discord.app_commands.Range[int, 1, 100]):
    success, msg = daily_checklist.remove_item(interaction.user.id, position)
    await interaction.response.send_message(msg, ephemeral=not success)


# Subcommand `/daily list`
@daily_command_group.command(name="list", description="List your daily checklist items")
@log_interaction
async def daily_list_slash_command(interaction: discord.Interaction):
    current_day = daily_checklist.get_current_day()
    items = daily_checklist.get_checklist_for_date(interaction.user.id, current_day)
    response = daily_checklist.format_checklist_response(items, current_day)
    await interaction.response.send_message(response)


# Subcommand `/daily check`
@daily_command_group.command(name="check", description="Mark an item as completed by its position")
@log_interaction
async def daily_check_slash_command(interaction: discord.Interaction, position: discord.app_commands.Range[int, 1, 100]):
    success, msg = daily_checklist.check_item(interaction.user.id, position)
    await interaction.response.send_message(msg)


# Subcommand `/daily uncheck`
@daily_command_group.command(name="uncheck", description="Remove completion mark from an item")
@log_interaction
async def daily_uncheck_slash_command(interaction: discord.Interaction, position: discord.app_commands.Range[int, 1, 100]):
    success, msg = daily_checklist.uncheck_item(interaction.user.id, position)
    await interaction.response.send_message(msg)


# Subcommand `/daily edit`
@daily_command_group.command(name="edit", description="Edit an item in your checklist")
@log_interaction
async def daily_edit_slash_command(interaction: discord.Interaction, position: discord.app_commands.Range[int, 1, 100]):
    items = daily_checklist.list_items(interaction.user.id)
    if not items or position > len(items):
        await interaction.response.send_message("Invalid index.", ephemeral=True)
        return
    
    await interaction.response.send_modal(
        daily_checklist.EditDailyItemModal(
            interaction.user.id,
            position,
            items[position-1].item
        )
    )


# Subcommand `/daily move`
@daily_command_group.command(name="move", description="Move an item to a different position")
@log_interaction
async def daily_move_slash_command(interaction: discord.Interaction, 
    old_position: discord.app_commands.Range[int, 1, 100],
    new_position: discord.app_commands.Range[int, 1, 100]):
    success, msg = daily_checklist.move_item(interaction.user.id, old_position, new_position)
    await interaction.response.send_message(msg)


# Subcommand `/daily history`
@daily_command_group.command(name="history", description="View your checklist for a specific date")
@log_interaction
async def daily_history_slash_command(interaction: discord.Interaction, date: str):  # Format: YYYY-MM-DD
    try:
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            target_date = daily_checklist.get_current_day()
    except ValueError:
        await interaction.response.send_message("Invalid date format. Please use YYYY-MM-DD", ephemeral=True)
        return

    items = daily_checklist.get_checklist_for_date(interaction.user.id, target_date)
    response = daily_checklist.format_checklist_response(items, target_date)
    await interaction.response.send_message(response)


# https://fallendeity.github.io/discord.py-masterclass/slash-commands/#error-handling-and-checks
@tree.error
async def on_error(interaction: discord.Interaction[discord.Client],
                   error: discord.app_commands.AppCommandError | Exception) -> None:
    print(error)
    if isinstance(error, discord.app_commands.errors.CommandInvokeError):
        error = error.original
    message = f"\nException: {error.__class__.__name__}, Error: {error}, Command: {interaction.command.qualified_name if interaction.command else None}, User: {interaction.user}, Time: {discord.utils.format_dt(interaction.created_at, style='F')}\n"

    if isinstance(error, InvalidInputError):
        message = error

    try:
        await interaction.response.send_message(f"An error occurred: {message}")
    except discord.InteractionResponded:
        await interaction.followup.send(f"An error occurred: {message}")


@tasks.loop(seconds=10)
async def check_reminders():
    now = datetime.now()
    reminders = Reminder.select().where(Reminder.remind_at <= now)

    for r in reminders:
        try:
            if r.is_private:
                user = await client.fetch_user(r.user_id)
                if user:
                    await user.send(f"⏰ Reminder: {r.message}")
            else:
                channel = client.get_channel(r.channel_id)
                if channel:
                    await channel.send(f"⏰ Reminder for <@{r.user_id}>: {r.message}")
                else:
                    # If channel is None, try sending as DM (for DM reminders)
                    user = await client.fetch_user(r.user_id)
                    if user:
                        await user.send(f"⏰ Reminder: {r.message}")

            # Delete the reminder after sending it
            r.delete_instance()

        except discord.NotFound:
            print(f"User {r.user_id} or Channel {r.channel_id} not found.")
        except discord.Forbidden:
            print(f"Cannot send message to {r.user_id} or Channel {r.channel_id} (they might have DMs or messages disabled).")
        except discord.HTTPException as e:
            print(f"Failed to send reminder to {r.user_id} or Channel {r.channel_id}: {e}")

@check_reminders.before_loop
async def before_check_reminders():
    await client.wait_until_ready()


client.run(config.discord_token)

