#!/usr/bin/env python3
import discord
from config import BOT_TOKEN

# Simple bot test to verify token validity
intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot connected successfully as {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print("Token is valid and bot is ready!")
    await bot.close()

@bot.event
async def on_connect():
    print("🔗 Bot is connecting to Discord...")

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN is not set or empty")
        exit(1)
    
    print(f"🚀 Testing bot connection with token length: {len(BOT_TOKEN)}")
    try:
        bot.run(BOT_TOKEN)
    except discord.LoginFailure as e:
        print(f"❌ Login failed: {e}")
        print("The bot token appears to be invalid or expired.")
        print("Please check your Discord Developer Portal and regenerate the token if needed.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")