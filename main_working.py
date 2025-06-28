# main_working.py - Рабочий Discord бот с полной функциональностью
import os
import discord
import datetime
import pytz
from dotenv import load_dotenv

# Импортируем наши модули
import database
import config

# Загружаем переменные окружения
load_dotenv()

# Настройка интентов для бота
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
intents.members = False

# Создание экземпляра бота с использованием py-cord
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
        static_id_value = self.static_id.value.strip() if self.static_id.value else None
        nickname_value = self.nickname.value.strip() if self.nickname.value else None
        
        if not static_id_value or not nickname_value:
            await interaction.response.send_message("❌ Заполните все поля!", ephemeral=True)
            return

        # Регистрируем игрока в базе данных
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
            try:
                await interaction.user.send(embed=embed)
                await interaction.response.send_message("✅ Проверьте личные сообщения!", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("❌ Вы уже зарегистрированы!", ephemeral=True)

class RegistrationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 Зарегистрироваться", style=discord.ButtonStyle.primary)
    async def register_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Кнопка для начала регистрации."""
        if interaction.guild and interaction.guild.id != config.GUILD_ID:
            await interaction.response.send_message("❌ Команда недоступна на этом сервере.", ephemeral=True)
            return
        
        # Проверяем, зарегистрирован ли уже игрок
        player = database.get_player(interaction.user.id)
        if player:
            await interaction.response.send_message("❌ Вы уже зарегистрированы!", ephemeral=True)
            return
        
        modal = RegistrationModal()
        await interaction.response.send_modal(modal)

@bot.event
async def on_ready():
    """Событие готовности бота."""
    print(f'{bot.user} подключен к Discord!')
    database.setup_database()
    print("База данных инициализирована.")

@bot.slash_command(name='start', description='Регистрация на ивент поиска локаций')
async def start_registration(ctx):
    """Слэш-команда для начала регистрации на ивент."""
    if ctx.guild and ctx.guild.id != config.GUILD_ID:
        await ctx.respond("❌ Команда недоступна на этом сервере.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="***Ивент поиска локаций***",
        description="Нажмите кнопку ниже для регистрации на ивент!",
        color=config.RASPBERRY_COLOR
    )
    
    view = RegistrationView()
    await ctx.respond(embed=embed, view=view, ephemeral=True)

@bot.event
async def on_message(message):
    """Обработка сообщений в личных сообщениях (прием скриншотов)."""
    
    # Игнорируем сообщения не в ЛС или от самого бота
    if message.guild is not None or message.author == bot.user:
        return
    
    # Проверяем, зарегистрирован ли пользователь
    player = database.get_player(message.author.id)
    if not player:
        return
    
    # Проверяем, не дисквалифицирован ли игрок
    if database.is_player_disqualified(message.author.id):
        await message.reply("❌ Вы были дисквалифицированы.")
        return
    
    # Проверяем, активен ли ивент
    if not is_event_active():
        await message.reply("⏰ Событие сейчас неактивно.")
        return
    
    # Проверяем наличие вложений
    if not message.attachments:
        return
    
    # Проверяем, что вложение является изображением
    valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
    attachment = message.attachments[0]
    
    if not any(attachment.filename.lower().endswith(ext) for ext in valid_extensions):
        await message.reply("❌ Пожалуйста, отправьте изображение в формате PNG, JPG, JPEG, GIF или WebP.")
        return
    
    # Сохраняем скриншот в базе данных
    success = database.add_submission(player['id'], attachment.url)
    
    if success:
        # Получаем количество отправленных скриншотов
        submissions = database.get_player_submissions(message.author.id)
        count = len(submissions)
        
        embed = discord.Embed(
            title="✅ Скриншот принят!",
            description=f"Всего отправлено скриншотов: **{count}**",
            color=config.RASPBERRY_COLOR
        )
        embed.set_image(url=attachment.url)
        
        await message.reply(embed=embed)
    else:
        await message.reply("❌ Ошибка при сохранении скриншота. Попробуйте еще раз.")

async def has_admin_permissions(ctx) -> bool:
    """Проверка прав администратора на сервере."""
    if not ctx.guild:
        return False
    
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("❌ У вас нет прав администратора.", ephemeral=True)
        return False
    
    return True

class PlayerSelect(discord.ui.Select):
    def __init__(self, players_data):
        # Создаем опции для выпадающего меню
        options = []
        for player in players_data[:25]:  # Discord ограничивает до 25 опций
            discord_id, nickname, screenshot_count = player
            try:
                user = bot.get_user(discord_id)
                display_name = f"@{user.name}" if user else f"ID:{discord_id}"
            except:
                display_name = f"ID:{discord_id}"
            
            label = f"{nickname} ({display_name})"
            description = f"Скриншотов: {screenshot_count}"
            
            options.append(discord.SelectOption(
                label=label[:100],  # Ограничение Discord
                description=description[:100],
                value=str(discord_id)
            ))
        
        placeholder = "Выберите игрока для просмотра профиля..." if options else "Нет зарегистрированных игроков"
        
        super().__init__(
            placeholder=placeholder,
            options=options if options else [discord.SelectOption(label="Пусто", value="0")],
            disabled=not options
        )

    async def callback(self, interaction: discord.Interaction):
        """Обработка выбора игрока."""
        if self.disabled:
            return
            
        selected_discord_id = int(self.values[0])
        
        # Получаем данные игрока
        player = database.get_player(selected_discord_id)
        if not player:
            await interaction.response.send_message("❌ Игрок не найден.", ephemeral=True)
            return
        
        # Получаем скриншоты игрока
        submissions = database.get_player_submissions(selected_discord_id)
        
        user = bot.get_user(selected_discord_id)
        display_name = f"@{user.name}" if user else f"ID:{selected_discord_id}"
        
        embed = discord.Embed(
            title=f"👤 Профиль игрока",
            color=config.RASPBERRY_COLOR
        )
        embed.add_field(name="Никнейм", value=player['nickname'], inline=True)
        embed.add_field(name="Discord", value=display_name, inline=True)
        embed.add_field(name="StaticID", value=player['static_id'], inline=True)
        embed.add_field(name="Скриншотов", value=str(len(submissions)), inline=True)
        embed.add_field(name="Статус", value="❌ Дисквалифицирован" if player['is_disqualified'] else "✅ Активен", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class PlayerListView(discord.ui.View):
    def __init__(self, players_data):
        super().__init__(timeout=60)
        self.add_item(PlayerSelect(players_data))

@bot.slash_command(name='admin_stats', description='Статистика ивента (только для администраторов)')
async def admin_stats(ctx):
    """Слэш-команда для получения статистики ивента."""
    if not await has_admin_permissions(ctx):
        return
    
    # Получаем общую статистику
    total_players = database.get_all_players_stats()
    leaderboard = database.get_leaderboard()
    
    embed = discord.Embed(
        title="📊 Статистика ивента",
        color=config.RASPBERRY_COLOR
    )
    embed.add_field(name="👥 Всего игроков", value=str(total_players), inline=True)
    embed.add_field(name="🏆 Активных игроков", value=str(len(leaderboard)), inline=True)
    embed.add_field(name="📅 Период ивента", value=format_event_dates(), inline=False)
    embed.add_field(name="⏰ Статус", value="🟢 Активен" if is_event_active() else "🔴 Неактивен", inline=True)
    
    if leaderboard:
        view = PlayerListView(leaderboard)
        await ctx.respond(embed=embed, view=view, ephemeral=True)
    else:
        await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name='admin_profile', description='Просмотр профиля игрока (только для администраторов)')
async def admin_profile(ctx, user: discord.Member):
    """Слэш-команда для просмотра профиля игрока."""
    if not await has_admin_permissions(ctx):
        return
    
    # Получаем данные игрока
    player = database.get_player(user.id)
    if not player:
        await ctx.respond(f"❌ Пользователь {user.mention} не зарегистрирован.", ephemeral=True)
        return
    
    # Получаем скриншоты игрока
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
    
    if submissions:
        recent_submissions = submissions[-3:]  # Последние 3 скриншота
        embed.add_field(
            name="📸 Последние скриншоты",
            value="\n".join([f"[Скриншот {i+1}]({sub['screenshot_url']})" for i, sub in enumerate(recent_submissions)]),
            inline=False
        )
    
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name='admin_disqualify', description='Дисквалификация игрока (только для администраторов)')
async def admin_disqualify(ctx, user: discord.Member):
    """Слэш-команда для дисквалификации игрока."""
    if not await has_admin_permissions(ctx):
        return
    
    # Проверяем, зарегистрирован ли игрок
    player = database.get_player(user.id)
    if not player:
        await ctx.respond(f"❌ Пользователь {user.mention} не зарегистрирован.", ephemeral=True)
        return
    
    # Дисквалифицируем игрока
    success = database.disqualify_player(user.id)
    
    if success:
        embed = discord.Embed(
            title="⚠️ Игрок дисквалифицирован",
            description=f"Пользователь {user.mention} был дисквалифицирован.\nВсе его скриншоты помечены как недействительные.",
            color=0xFF0000
        )
        await ctx.respond(embed=embed, ephemeral=True)
        
        # Уведомляем игрока в ЛС
        try:
            dm_embed = discord.Embed(
                title="❌ Дисквалификация",
                description="Вы были дисквалифицированы с ивента поиска локаций.",
                color=0xFF0000
            )
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # Игнорируем, если нельзя отправить ЛС
    else:
        await ctx.respond("❌ Ошибка при дисквалификации.", ephemeral=True)

# Запуск бота
if __name__ == "__main__":
    token = config.BOT_TOKEN
    if token == "YOUR_BOT_TOKEN_HERE":
        print("Error: Please set BOT_TOKEN in environment variables")
    else:
        bot.run(token)