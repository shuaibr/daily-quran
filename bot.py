# bot.py
import os
import discord
import random
import sys
import logging
import asyncio
import datetime, timedelta
from datetime import datetime, timedelta

from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from database import DatabaseHandler

# Load environment variables
load_dotenv()

# Retrieve Discord token and other environment variables
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
DB_HOST = os.getenv('DB_HOST')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_USER = os.getenv('DB_USER')
DB_PORT = os.getenv('DB_PORT')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Maximum length of a message
MAX_MESSAGE_LEN = 1900
now = datetime.now()
# Time for daily Quran Update
TARGET_HOUR =now.hour
TARGET_MINUTE = now.minute +1 

# Default Quran edition
EDITION_FIXED = 'eng-abdelhaleem'

# Initialize DatabaseHandler with database URL
db_url = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}'
db_handler = DatabaseHandler(db_url)

# Initialize Discord bot
# bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())
bot = commands.Bot(command_prefix=commands.when_mentioned_or('/'), intents=discord.Intents.all())
# bot = commands.Bot(command_prefix="/")

# slash = SlashCommand(bot, sync_commands=True)

def get_default_chapter():
    """Returns a random chapter number within a specific range."""
    return random.randint(67, 114)

def get_verse_markers(total_verses, verse_start, verse_end):
    """Calculates verse start and end based on user input."""
    verse_start = int(verse_start)-1 if verse_start and int(verse_start)-1 < total_verses and int(verse_start)-1>0 else 0
    verse_end = int(verse_end)-1 if verse_end and int(verse_end)-1 < total_verses and int(verse_end) > verse_start else total_verses

    return verse_start, verse_end

def get_message(chapter, edition_name, verse_start, verse_end):
    """Retrieves Quran verses based on the specified chapter, edition, and user input."""
    sql_query = 'SELECT * from verse where edition_name=:edition AND chapter=:chapter ORDER BY verse ASC'

    # Execute the SQL query using the DatabaseHandler
    result = db_handler.execute_query(sql_query, {'edition': edition_name, 'chapter': chapter})

    total_verses = len(result)

    verse_start, verse_end = get_verse_markers(total_verses, verse_start, verse_end)

    result = result[verse_start: verse_end]

    # Create a message by joining verses
    message = f"### Chapter {chapter}, Verses {verse_start + 1} to {verse_end+1}, Edition: {edition_name}\n```"
    message += "\n".join(row[4] for row in result)

    link = get_quran_link(chapter, verse_start)

    if len(message) > MAX_MESSAGE_LEN:
        # Truncate the message if it exceeds the maximum length
        verse_too_long_msg = '[Click here to visit the full chapter]({})'.format(link)
        truncated_message = message[:MAX_MESSAGE_LEN] 
        last_period_index = truncated_message.rfind('.')
        if last_period_index != -1:
            message = truncated_message[:last_period_index + 1] + "```" + verse_too_long_msg
    else:
        message += '```'
        
    return message

def get_quran_link(chapter, verse_start):
    link = '<https://quran.com/{}?startingVerse={}>'.format(chapter, verse_start)
    return link


@bot.event
async def on_ready():
    """Prints a message when the bot is successfully logged in."""
    print(f'We have logged in as {bot.user}')
    channel_name = 'welcome'
    channel = discord.utils.get(bot.get_all_channels(), name=channel_name)

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.event
async def on_message(message):
    """Event listener for processing every message."""
    if message.author == bot.user:
        return  # Ignore messages sent by the bot itself

    # print("By: ", message.author," Message: ", message.content)

    await bot.process_commands(message)  # Ensure that commands are processed as well

@bot.event
async def on_command_error(ctx, error):
    """Event listener for handling errors raised during command execution."""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore messages with no valid command

    # Your custom error handling logic goes here
    logging.error(f'An error occurred: {error}', exc_info=True)
    await ctx.send(f'An error occurred: {error}')

@bot.tree.command(name="hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hey {interaction.user.mention}! This is a slash command", ephemeral=True)

# @bot.tree.command(name="quran", description = "Get a random verse")
# async def quran(interaction: discord.Interaction, chapter: Optional(chapter), verse_start: Optional(verse_start), verse_end: Optional(verse_end)):
#     """Command to retrieve and send Quran verses."""
#     try:
#         edition_name = EDITION_FIXED
#         if not chapter:
#             chapter = get_default_chapter()

#         message = get_message(chapter, edition_name, verse_start, verse_end)

#         await interaction.response.send_message(message)
#     except Exception as e:
#         # Log errors and inform the user about the issue
#         logging.error(f'An error occurred: {e}', exc_info=True)
#         await interaction.response.send_message("An error occurred while processing your request.")

@bot.tree.command(name="say")
@app_commands.describe(thing_to_say = "What should I say?")
async def say(interaction: discord.Interaction, thing_to_say: str):
    await interaction.response.send_message(f"{interaction.user.name} said: `{thing_to_say}`")

@bot.command()
async def quran(ctx,
    chapter=None,
    verse_start=None,
    verse_end=None):
    """Command to retrieve and send Quran verses."""
    try:
        edition_name = EDITION_FIXED
        chapter = chapter or get_default_chapter()

        message = get_message(chapter, edition_name, verse_start, verse_end)

        print("Message length: ", len(message))

        await ctx.send(message)
    except Exception as e:
        # Log errors and inform the user about the issue
        logging.error(f'An error occurred: {e}', exc_info=True)
        await ctx.send("An error occurred while processing your request.")

# @bot.group(name='quran', invoke_without_command=True)
# async def quran(ctx):
#     """Base command for Quran-related commands."""
#     await ctx.send("Please specify a subcommand. Use `/quran help` for more information.")

# @quran.command(name='verse')
# async def quran_verse(ctx, chapter: int, verse_start: int, verse_end: int):
#     """Retrieve and send Quran verses."""
#     try:
#         edition_name = 'eng-abdelhaleem'  # Replace with your desired edition
#         message = get_message(chapter, edition_name, [chapter, verse_start, verse_end])
#         await ctx.send(message)
#     except Exception as e:
#         # Log errors and inform the user about the issue
#         logging.error(f'An error occurred: {e}', exc_info=True)
#         await ctx.send("An error occurred while processing your request.")

# @quran.command(name='chapter')
# async def quran_chapter(ctx, chapter: int):
#     """Get a summary or overview of a specific chapter."""
#     # Implement chapter overview logic here

# @quran.command(name='random')
# async def quran_random(ctx):
#     """Generate and display a random verse."""
#     # Implement random verse logic here
async def send_message(error=None):
    channel_name = 'welcome'
    channel = discord.utils.get(bot.get_all_channels(), name=channel_name)
    message = "**Quran Daily**\n"
    message += get_message(get_default_chapter(), EDITION_FIXED, None, None)
    
    if not error and channel:
        await channel.send(message)
    else:
        await channel.send(error)

# @bot.event
# async def on_message(message):
#     if message.author == bot.user:
#         return

#     await bot.process_commands(message)

# Schedule the task to send a message every minute
# async def my_background_task():
#     try:
#         await bot.wait_until_ready()
#         while not bot.is_closed():
#             await send_message()
#             await asyncio.sleep(10)  # sleep for 60 seconds (1 minute)
#     except Exception as e:
#         # Log errors and inform the user about the issue
#         logging.error(f'An error occurred: {e}', exc_info=True)
#         await send_message("An error occurred while processing your request.")


async def my_background_task():
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        # Calculate time until the next occurrence of the target hour
        current_time = datetime.now()
        target_time = datetime(current_time.year, current_time.month, current_time.day, TARGET_HOUR, TARGET_MINUTE, 0)
                
        if current_time >= target_time:
            target_time += timedelta(days=1)  # If the target hour has already passed, schedule for the next day
        time_until_target = target_time - current_time
        seconds_until_target = time_until_target.total_seconds()
        
        await asyncio.sleep(seconds_until_target)
        
        await send_message()

bot.add_listener(my_background_task, 'on_ready')
# Run the bot
bot.run(TOKEN)
