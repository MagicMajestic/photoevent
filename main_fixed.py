import os
import discord
import datetime
import pytz
from dotenv import load_dotenv

# Импортируем наши модули
import database
import config

load_dotenv()

# Настройка интентов для бота
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

# Создание экземпляра бота
bot = discord.Bot(intents=intents)

def is_event_active() -> bool:
    """Проверяет, активен ли ивент в настоящее время."""
    try:
        start_time = datetime.datetime.fromisoformat(config.EVENT_START_TIME.replace('Z', '+00:00'))
        end_time = datetime.datetime.fromisoformat(config.EVENT_END_TIME.replace('Z', '+00:00'))
        current_time = datetime.datetime.now(pytz.UTC)
        return start_time <= current_time <= end_time
    except Exception:
        return False

def format_event_dates() -> str:
    """Форматирует даты начала и конца ивента для отображения."""
    try:
        start_time = datetime.datetime.fromisoformat(config.EVENT_START_TIME.replace('Z', '+00:00'))
        end_time = datetime.datetime.fromisoformat(config.EVENT_END_TIME.replace('Z', '+00:00'))
        start_str = start_time.strftime("%d.%m.%Y в %H:%M")
        end_str = end_time.strftime("%d.%m.%Y в %H:%M")
        return f"{start_str} до {end_str}"
    except Exception:
        return "Ошибка в конфигурации дат"

class RegistrationModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Регистрация на ивент")
        
    static_id = discord.ui.InputText(
        label='Ваш StaticID',
        placeholder='Введите ваш StaticID',
        required=True,
        max_length=50
    )
    
    nickname = discord.ui.InputText(
        label='Ваш игровой Nickname',
        placeholder='Введите ваш игровой никнейм',
        required=True,
        max_length=50
    )

    async def callback(self, interaction: discord.Interaction):
        """Обработка отправки формы регистрации."""
        try:
            static_id_value = self.static_id.value.strip() if self.static_id.value else None
            nickname_value = self.nickname.value.strip() if self.nickname.value else None
            
            if not static_id_value or not nickname_value:
                await interaction.response.send_message("❌ Заполните все поля!", ephemeral=True)
                return

            success = database.register_player(interaction.user.id, static_id_value, nickname_value)
            
            if success:
                embed = discord.Embed(
                    title="✅ Регистрация успешна!",
                    description=f"**StaticID:** {static_id_value}\n**Nickname:** {nickname_value}\n\n**Период ивента:** {format_event_dates()}",
                    color=config.RASPBERRY_COLOR
                )
                embed.add_field(
                    name="📩 Отправка скриншотов",
                    value="Теперь отправляйте скриншоты в личные сообщения боту во время проведения ивента.",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Вы уже зарегистрированы!", ephemeral=True)
        except Exception as e:
            print(f"Ошибка в регистрации: {e}")
            await interaction.response.send_message("❌ Произошла ошибка при регистрации.", ephemeral=True)

class RegistrationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Зарегистрироваться", style=discord.ButtonStyle.primary)
    async def register_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Кнопка для начала регистрации."""
        try:
            player = database.get_player(interaction.user.id)
            if player:
                await interaction.response.send_message("❌ Вы уже зарегистрированы!", ephemeral=True)
                return
            
            modal = RegistrationModal()
            await interaction.response.send_modal(modal)
        except Exception as e:
            print(f"Ошибка кнопки регистрации: {e}")
            await interaction.response.send_message("❌ Произошла ошибка.", ephemeral=True)

@bot.event
async def on_ready():
    """Событие готовности бота."""
    print(f'{bot.user} подключен к Discord!')
    database.setup_database()
    print("База данных инициализирована.")

@bot.slash_command(name='start', description='Регистрация на ивент поиска локаций', guild_ids=[config.GUILD_ID])
async def start_registration(ctx):
    """Команда для начала регистрации на ивент."""
    try:
        embed = discord.Embed(
            title="***Ивент поиска локаций***",
            description="Нажмите кнопку ниже для регистрации на ивент!",
            color=config.RASPBERRY_COLOR
        )
        
        view = RegistrationView()
        await ctx.respond(embed=embed, view=view, ephemeral=True)
    except Exception as e:
        print(f"Ошибка команды /start: {e}")
        await ctx.respond("❌ Произошла ошибка.", ephemeral=True)

@bot.event
async def on_message(message):
    """Обработка сообщений в личных сообщениях (прием скриншотов)."""
    try:
        if message.guild is not None or message.author == bot.user:
            return
        
        player = database.get_player(message.author.id)
        if not player:
            return
        
        if database.is_player_disqualified(message.author.id):
            await message.reply("❌ Вы были дисквалифицированы.")
            return
        
        if not is_event_active():
            await message.reply("⏰ Событие сейчас неактивно.")
            return
        
        if not message.attachments:
            return
        
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
        attachment = message.attachments[0]
        
        if not any(attachment.filename.lower().endswith(ext) for ext in valid_extensions):
            await message.reply("❌ Пожалуйста, отправьте изображение в формате PNG, JPG, JPEG, GIF или WebP.")
            return
        
        success = database.add_submission(player['id'], attachment.url)
        
        if success:
            submissions = database.get_player_submissions(message.author.id)
            count = len(submissions)
            
            embed = discord.Embed(
                title="✅ Скриншот принят!",
                description=f"Всего отправлено скриншотов: **{count}**\nСтатус: ⏳ На модерации",
                color=config.RASPBERRY_COLOR
            )
            embed.set_image(url=attachment.url)
            
            await message.reply(embed=embed)
        else:
            await message.reply("❌ Ошибка при сохранении скриншота. Попробуйте еще раз.")
    except Exception as e:
        print(f"Ошибка обработки сообщения: {e}")

async def has_admin_permissions(ctx) -> bool:
    """Проверка прав администратора на сервере."""
    if not ctx.guild:
        return False
    
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("❌ У вас нет прав администратора.", ephemeral=True)
        return False
    
    return True

@bot.slash_command(name='admin_stats', description='Статистика ивента (только для администраторов)', guild_ids=[config.GUILD_ID])
async def admin_stats(ctx):
    """Команда для получения статистики ивента."""
    try:
        if not await has_admin_permissions(ctx):
            return
        
        total_players = database.get_all_players_stats()
        leaderboard = database.get_leaderboard()
        
        # Считаем общую статистику
        total_submissions = sum(player[2] for player in leaderboard)
        
        embed = discord.Embed(
            title="📊 Статистика ивента",
            color=config.RASPBERRY_COLOR
        )
        embed.add_field(name="👥 Всего игроков", value=str(total_players), inline=True)
        embed.add_field(name="🏆 Активных игроков", value=str(len(leaderboard)), inline=True)
        embed.add_field(name="📸 Всего скриншотов", value=str(total_submissions), inline=True)
        embed.add_field(name="📅 Период ивента", value=format_event_dates(), inline=False)
        embed.add_field(name="⏰ Статус", value="🟢 Активен" if is_event_active() else "🔴 Неактивен", inline=True)
        
        # Показываем топ-5 игроков
        if leaderboard:
            top_players = leaderboard[:5]
            top_text = ""
            for i, (discord_id, nickname, count) in enumerate(top_players, 1):
                top_text += f"{i}. {nickname} - {count} скриншотов\n"
            embed.add_field(name="🏆 Топ-5 игроков", value=top_text or "Нет данных", inline=False)
        
        await ctx.respond(embed=embed, ephemeral=True)
    except Exception as e:
        print(f"Ошибка команды /admin_stats: {e}")
        await ctx.respond("❌ Произошла ошибка.", ephemeral=True)

@bot.slash_command(name='admin_profile', description='Просмотр профиля игрока (только для администраторов)', guild_ids=[config.GUILD_ID])
async def admin_profile(ctx, user: discord.Member):
    """Команда для просмотра профиля игрока."""
    try:
        if not await has_admin_permissions(ctx):
            return
        
        player = database.get_player(user.id)
        if not player:
            await ctx.respond(f"❌ Пользователь {user.mention} не зарегистрирован.", ephemeral=True)
            return
        
        submissions = database.get_player_submissions(user.id)
        
        embed = discord.Embed(
            title=f"👤 Профиль игрока",
            color=config.RASPBERRY_COLOR
        )
        embed.add_field(name="Никнейм", value=player['nickname'], inline=True)
        embed.add_field(name="Discord", value=f"@{user.name}", inline=True)
        embed.add_field(name="StaticID", value=player['static_id'], inline=True)
        embed.add_field(name="Скриншотов", value=str(len(submissions)), inline=True)
        embed.add_field(name="Статус", value="❌ Дисквалифицирован" if player['is_disqualified'] else "✅ Активен", inline=True)
        
        await ctx.respond(embed=embed, ephemeral=True)
    except Exception as e:
        print(f"Ошибка команды /admin_profile: {e}")
        await ctx.respond("❌ Произошла ошибка.", ephemeral=True)

@bot.slash_command(name='admin_disqualify', description='Дисквалификация игрока (только для администраторов)', guild_ids=[config.GUILD_ID])
async def admin_disqualify(ctx, user: discord.Member):
    """Команда для дисквалификации игрока."""
    try:
        if not await has_admin_permissions(ctx):
            return
        
        player = database.get_player(user.id)
        if not player:
            await ctx.respond(f"❌ Пользователь {user.mention} не зарегистрирован.", ephemeral=True)
            return
        
        success = database.disqualify_player(user.id)
        
        if success:
            embed = discord.Embed(
                title="⚠️ Игрок дисквалифицирован",
                description=f"Пользователь {user.mention} был дисквалифицирован.\nВсе его скриншоты помечены как недействительные.",
                color=0xFF0000
            )
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            await ctx.respond("❌ Ошибка при дисквалификации.", ephemeral=True)
    except Exception as e:
        print(f"Ошибка команды /admin_disqualify: {e}")
        await ctx.respond("❌ Произошла ошибка.", ephemeral=True)

# Запуск бота
if __name__ == "__main__":
    token = config.BOT_TOKEN
    if token == "YOUR_BOT_TOKEN_HERE":
        print("Error: Please set BOT_TOKEN in environment variables")
    else:
        bot.run(token)