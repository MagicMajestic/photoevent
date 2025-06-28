#!/usr/bin/env python3
# Test script to check py-cord installation
try:
    import discord
    print(f"Discord version: {discord.__version__}")
    print(f"Has Bot: {hasattr(discord, 'Bot')}")
    print(f"Has ApplicationContext: {hasattr(discord, 'ApplicationContext')}")
    print(f"Has SlashCommandGroup: {hasattr(discord, 'SlashCommandGroup')}")
    print(f"Has ui.InputText: {hasattr(discord.ui, 'InputText')}")
    
    # Try to create a bot instance
    intents = discord.Intents.default()
    bot = discord.Bot(intents=intents)
    print("✅ Bot instance created successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    
# Also check if py-cord is properly installed
try:
    from discord import __version__ as discord_version
    print(f"Discord module version: {discord_version}")
except ImportError as e:
    print(f"❌ Import error: {e}")