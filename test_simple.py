import os
import discord
from dotenv import load_dotenv

load_dotenv()

# Настройка интентов
intents = discord.Intents.default()
intents.message_content = True

# Создание бота
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} готов к работе!')
    print(f'Подключен к {len(bot.guilds)} серверам')
    for guild in bot.guilds:
        print(f'- {guild.name} (ID: {guild.id})')

@bot.slash_command(name="test", description="Тестовая команда")
async def test_command(ctx):
    await ctx.respond("Команда работает!", ephemeral=True)

@bot.slash_command(name="ping", description="Проверка связи")
async def ping(ctx):
    await ctx.respond(f"Понг! Задержка: {round(bot.latency * 1000)}ms", ephemeral=True)

# Запуск бота
if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if token:
        bot.run(token)
    else:
        print("Ошибка: BOT_TOKEN не найден")