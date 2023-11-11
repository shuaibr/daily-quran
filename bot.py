# bot.py
import os
import discord
import random
import sys
import logging
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
MAX_MESSAGE_LEN = 2000

# Default Quran edition
EDITION_FIXED = 'eng-abdelhaleem'

# Initialize DatabaseHandler with database URL
db_url = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}'
db_handler = DatabaseHandler(db_url)

# Initialize Discord bot
# bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())
bot = commands.Bot(command_prefix=commands.when_mentioned_or('/'), intents=discord.Intents.all())

def get_default_chapter():
    """Returns a random chapter number within a specific range."""
    return random.randint(67, 114)

def get_verse_markers(total_verses, arr):
    """Calculates verse start and end based on user input."""
    verse_start = 0
    verse_end = total_verses

    if len(arr) >= 2 and int(arr[1]) > 0:
        verse_start = int(arr[1])-1 if int(arr[1])-1 < total_verses else 0
    if len(arr) == 3 and int(arr[2]) >= verse_start:
        verse_end = int(arr[2])-1 if int(arr[2])-1 < total_verses else total_verses

    if verse_start > verse_end:
        verse_start = verse_end

    return verse_start, verse_end

def get_message(chapter, edition_name, arr):
    """Retrieves Quran verses based on the specified chapter, edition, and user input."""
    sql_query = 'SELECT * from verse where edition_name=:edition AND chapter=:chapter ORDER BY verse ASC'

    # Execute the SQL query using the DatabaseHandler
    result = db_handler.execute_query(sql_query, {'edition': edition_name, 'chapter': chapter})

    total_verses = len(result)

    verse_start, verse_end = get_verse_markers(total_verses, arr)

    result = result[verse_start: verse_end]

    # Create a message by joining verses
    message = "\n".join(row[4] for row in result)
    if len(message) > MAX_MESSAGE_LEN:
        # Truncate the message if it exceeds the maximum length
        truncated_message = message[:MAX_MESSAGE_LEN]
        last_period_index = truncated_message.rfind('.')
        if last_period_index != -1:
            message = truncated_message[:last_period_index + 1]

    return message

@bot.event
async def on_ready():
    """Prints a message when the bot is successfully logged in."""
    print(f'We have logged in as {bot.user}')
    channel_name = 'welcome'
    channel = discord.utils.get(bot.get_all_channels(), name=channel_name)

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

@bot.command()
async def quran(ctx, *arr):
    """Command to retrieve and send Quran verses."""
    try:
        edition_name = EDITION_FIXED
        if arr and int(arr[0]) > 0 and int(arr[0]) <= 114:
            chapter = int(arr[0])
        else:
            chapter = get_default_chapter()

        message = get_message(chapter, edition_name, arr)

        await ctx.send(message)
    except Exception as e:
        # Log errors and inform the user about the issue
        logging.error(f'An error occurred: {e}', exc_info=True)
        await ctx.send("An error occurred while processing your request.")

# Run the bot
bot.run(TOKEN)
