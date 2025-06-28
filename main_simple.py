# main_simple.py - Simple Discord bot for testing
import os
import discord
from dotenv import load_dotenv
import database
import config

# Load environment variables
load_dotenv()

# Setup intents
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

# Create bot instance
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    """Bot ready event."""
    print(f'{bot.user} connected to Discord!')
    
    # Initialize database
    database.setup_database()
    print("Database initialized.")

@bot.slash_command(name='test', description='Test command')
async def test_command(ctx):
    """Test slash command."""
    await ctx.respond("Bot is working!", ephemeral=True)

@bot.slash_command(name='start', description='Registration for event')
async def start_registration(ctx):
    """Start registration command."""
    embed = discord.Embed(
        title="Event Registration",
        description="Registration system is working!",
        color=config.RASPBERRY_COLOR
    )
    await ctx.respond(embed=embed, ephemeral=True)

# Run the bot
if __name__ == "__main__":
    token = config.BOT_TOKEN
    if token == "YOUR_BOT_TOKEN_HERE":
        print("Error: Please set BOT_TOKEN in environment variables")
    else:
        bot.run(token)