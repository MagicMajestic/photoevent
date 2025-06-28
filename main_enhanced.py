# main_enhanced.py - Улучшенный Discord бот с полной функциональностью
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

def get_user_tag(user_id: int) -> str:
    """Получает Discord тег пользователя или ID если не найден."""
    try:
        user = bot.get_user(user_id)
        if user:
            return f"@{user.name}"
        else:
            return f"ID:{user_id}"
    except:
        return f"ID:{user_id}"

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
        
        player = database.get_player(interaction.user.id)
        if player:
            await interaction.response.send_message("❌ Вы уже зарегистрированы!", ephemeral=True)
            return
        
        modal = RegistrationModal()
        await interaction.response.send_modal(modal)

# Классы для просмотра скриншотов
class ScreenshotSelect(discord.ui.Select):
    def __init__(self, submissions, player_info):
        self.submissions = submissions
        self.player_info = player_info
        
        options = []
        for i, sub in enumerate(submissions[:25]):  # Discord limit 25
            timestamp = datetime.datetime.fromisoformat(sub['submission_time'])
            date_str = timestamp.strftime("%d.%m %H:%M")
            
            status_emoji = "✅" if sub['is_approved'] else ("⏳" if sub['is_valid'] else "❌")
            label = f"Скриншот #{i+1} ({date_str})"
            description = f"{status_emoji} {'Одобрен' if sub['is_approved'] else ('На модерации' if sub['is_valid'] else 'Отклонен')}"
            
            options.append(discord.SelectOption(
                label=label[:100],
                description=description[:100], 
                value=str(sub['submission_id'])
            ))
        
        placeholder = "Выберите скриншот для просмотра..." if options else "Нет скриншотов"
        
        super().__init__(
            placeholder=placeholder,
            options=options if options else [discord.SelectOption(label="Пусто", value="0")],
            disabled=not options
        )

    async def callback(self, interaction: discord.Interaction):
        if self.disabled:
            return
            
        submission_id = int(self.values[0])
        submission = database.get_submission_by_id(submission_id)
        
        if not submission:
            await interaction.response.send_message("❌ Скриншот не найден.", ephemeral=True)
            return
        
        timestamp = datetime.datetime.fromisoformat(submission['submission_time'])
        date_str = timestamp.strftime("%d.%m.%Y в %H:%M")
        
        status_text = "✅ Одобрен" if submission['is_approved'] else ("⏳ На модерации" if submission['is_valid'] else "❌ Отклонен")
        
        embed = discord.Embed(
            title=f"📸 Скриншот #{submission_id}",
            description=f"**Игрок:** {self.player_info['nickname']}\n**Дата:** {date_str}\n**Статус:** {status_text}",
            color=config.RASPBERRY_COLOR
        )
        embed.set_image(url=submission['screenshot_url'])
        
        # Добавляем кнопки модерации только для админов
        view = ScreenshotModerationView(submission_id, submission['is_approved']) if await is_admin(interaction.user, interaction.guild) else None
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ScreenshotModerationView(discord.ui.View):
    def __init__(self, submission_id, current_status):
        super().__init__(timeout=300)
        self.submission_id = submission_id
        self.current_status = current_status
        
        # Добавляем кнопки в зависимости от текущего статуса
        if not current_status:
            self.add_item(discord.ui.Button(label="✅ Одобрить", style=discord.ButtonStyle.success, custom_id=f"approve_{submission_id}"))
        self.add_item(discord.ui.Button(label="❌ Отклонить", style=discord.ButtonStyle.danger, custom_id=f"reject_{submission_id}"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await is_admin(interaction.user, interaction.guild)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

# Обновленный класс выбора игроков
class PlayerSelect(discord.ui.Select):
    def __init__(self, players_data):
        options = []
        for player in players_data[:25]:
            discord_id, nickname, screenshot_count = player
            display_name = get_user_tag(discord_id)
            
            label = f"{nickname} ({display_name})"
            description = f"Скриншотов: {screenshot_count}"
            
            options.append(discord.SelectOption(
                label=label[:100],
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
        if self.disabled:
            return
            
        selected_discord_id = int(self.values[0])
        player = database.get_player(selected_discord_id)
        if not player:
            await interaction.response.send_message("❌ Игрок не найден.", ephemeral=True)
            return
        
        submissions = database.get_player_submissions(selected_discord_id)
        approved_count = len([s for s in submissions if s['is_approved']])
        
        embed = discord.Embed(
            title=f"👤 Профиль игрока",
            color=config.RASPBERRY_COLOR
        )
        embed.add_field(name="Никнейм", value=player['nickname'], inline=True)
        embed.add_field(name="Discord", value=get_user_tag(selected_discord_id), inline=True)
        embed.add_field(name="StaticID", value=player['static_id'], inline=True)
        embed.add_field(name="Скриншотов", value=str(len(submissions)), inline=True)
        embed.add_field(name="Одобрено", value=str(approved_count), inline=True)
        embed.add_field(name="Статус", value="❌ Дисквалифицирован" if player['is_disqualified'] else "✅ Активен", inline=True)
        
        # Добавляем выбор скриншотов если они есть
        view = None
        if submissions:
            view = PlayerProfileView(submissions, player)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class PlayerProfileView(discord.ui.View):
    def __init__(self, submissions, player_info):
        super().__init__(timeout=300)
        self.add_item(ScreenshotSelect(submissions, player_info))

class PlayerListView(discord.ui.View):
    def __init__(self, players_data):
        super().__init__(timeout=60)
        self.add_item(PlayerSelect(players_data))

async def is_admin(user, guild) -> bool:
    """Проверка прав администратора."""
    if not guild:
        return False
    return user.guild_permissions.administrator

async def has_admin_permissions(ctx) -> bool:
    """Проверка прав администратора на сервере."""
    if not ctx.guild:
        return False
    
    if not ctx.author.guild_permissions.administrator:
        await ctx.respond("❌ У вас нет прав администратора.", ephemeral=True)
        return False
    
    return True

@bot.event
async def on_ready():
    """Событие готовности бота."""
    print(f'{bot.user} подключен к Discord!')
    database.setup_database()
    print("База данных инициализирована.")
    
    # Синхронизируем slash-команды
    try:
        print("Команды зарегистрированы автоматически")
    except Exception as e:
        print(f"Ошибка: {e}")

@bot.slash_command(name='start', description='Регистрация на ивент поиска локаций', guild_ids=[config.GUILD_ID])
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

@bot.slash_command(name='admin_stats', description='Статистика ивента (только для администраторов)', guild_ids=[config.GUILD_ID])
async def admin_stats(ctx):
    """Слэш-команда для получения статистики ивента."""
    if not await has_admin_permissions(ctx):
        return
    
    total_players = database.get_all_players_stats()
    leaderboard = database.get_leaderboard()
    approved_stats = database.get_approved_screenshots_stats()
    
    # Считаем общую статистику
    total_submissions = sum(player[2] for player in leaderboard)
    total_approved = sum(player[3] for player in approved_stats)
    
    embed = discord.Embed(
        title="📊 Статистика ивента",
        color=config.RASPBERRY_COLOR
    )
    embed.add_field(name="👥 Всего игроков", value=str(total_players), inline=True)
    embed.add_field(name="🏆 Активных игроков", value=str(len(leaderboard)), inline=True)
    embed.add_field(name="📸 Всего скриншотов", value=str(total_submissions), inline=True)
    embed.add_field(name="✅ Одобренных скриншотов", value=str(total_approved), inline=True)
    embed.add_field(name="📅 Период ивента", value=format_event_dates(), inline=False)
    embed.add_field(name="⏰ Статус", value="🟢 Активен" if is_event_active() else "🔴 Неактивен", inline=True)
    
    # Показываем топ-5 игроков
    if leaderboard:
        top_players = leaderboard[:5]
        top_text = ""
        for i, (discord_id, nickname, count) in enumerate(top_players, 1):
            user_tag = get_user_tag(discord_id)
            top_text += f"{i}. {nickname} ({user_tag}) - {count} скриншотов\n"
        embed.add_field(name="🏆 Топ-5 игроков", value=top_text or "Нет данных", inline=False)
    
    view = PlayerListView(leaderboard) if leaderboard else None
    await ctx.respond(embed=embed, view=view, ephemeral=True)

@bot.slash_command(name='admin_profile', description='Просмотр профиля игрока (только для администраторов)', guild_ids=[config.GUILD_ID])
async def admin_profile(ctx, user: discord.Member):
    """Слэш-команда для просмотра профиля игрока."""
    if not await has_admin_permissions(ctx):
        return
    
    player = database.get_player(user.id)
    if not player:
        await ctx.respond(f"❌ Пользователь {user.mention} не зарегистрирован.", ephemeral=True)
        return
    
    submissions = database.get_player_submissions(user.id)
    approved_count = len([s for s in submissions if s['is_approved']])
    
    embed = discord.Embed(
        title=f"👤 Профиль игрока",
        color=config.RASPBERRY_COLOR
    )
    embed.add_field(name="Никнейм", value=player['nickname'], inline=True)
    embed.add_field(name="Discord", value=f"@{user.name}", inline=True)
    embed.add_field(name="StaticID", value=player['static_id'], inline=True)
    embed.add_field(name="Скриншотов", value=str(len(submissions)), inline=True)
    embed.add_field(name="Одобрено", value=str(approved_count), inline=True)
    embed.add_field(name="Статус", value="❌ Дисквалифицирован" if player['is_disqualified'] else "✅ Активен", inline=True)
    
    view = PlayerProfileView(submissions, player) if submissions else None
    await ctx.respond(embed=embed, view=view, ephemeral=True)

@bot.slash_command(name='admin_disqualify', description='Дисквалификация игрока (только для администраторов)', guild_ids=[config.GUILD_ID])
async def admin_disqualify(ctx, user: discord.Member):
    """Слэш-команда для дисквалификации игрока."""
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
        
        try:
            dm_embed = discord.Embed(
                title="❌ Дисквалификация",
                description="Вы были дисквалифицированы с ивента поиска локаций.",
                color=0xFF0000
            )
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass
    else:
        await ctx.respond("❌ Ошибка при дисквалификации.", ephemeral=True)

@bot.slash_command(name='calculate', description='Расчет выплат для одобренных скриншотов (только для администраторов)', guild_ids=[config.GUILD_ID])
async def calculate_payments(ctx):
    """Слэш-команда для расчета выплат."""
    if not await has_admin_permissions(ctx):
        return
    
    approved_stats = database.get_approved_screenshots_stats()
    
    if not approved_stats:
        await ctx.respond("❌ Нет одобренных скриншотов для расчета.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="💰 Расчет выплат",
        description="Команды для выдачи денег участникам:",
        color=config.RASPBERRY_COLOR
    )
    
    commands_text = ""
    total_amount = 0
    
    for discord_id, nickname, static_id, approved_count in approved_stats:
        amount = approved_count * 10000
        total_amount += amount
        commands_text += f"/givemoney {static_id} {amount} EventMagic\n"
    
    embed.add_field(name="📋 Команды", value=f"```{commands_text}```", inline=False)
    embed.add_field(name="💵 Общая сумма", value=f"{total_amount:,} $", inline=True)
    embed.add_field(name="👥 Участников", value=str(len(approved_stats)), inline=True)
    
    await ctx.respond(embed=embed, ephemeral=True)

# Обработка интерактивных элементов (кнопки модерации)
@bot.event
async def on_interaction(interaction):
    """Обработка взаимодействий с кнопками."""
    if interaction.type != discord.InteractionType.component:
        return
    
    custom_id = interaction.data.get('custom_id', '')
    
    if custom_id.startswith('approve_'):
        submission_id = int(custom_id.split('_')[1])
        success = database.approve_screenshot(submission_id)
        
        if success:
            await interaction.response.send_message("✅ Скриншот одобрен!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Ошибка при одобрении.", ephemeral=True)
    
    elif custom_id.startswith('reject_'):
        submission_id = int(custom_id.split('_')[1])
        success = database.reject_screenshot(submission_id)
        
        if success:
            await interaction.response.send_message("❌ Скриншот отклонен!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Ошибка при отклонении.", ephemeral=True)

# Запуск бота
if __name__ == "__main__":
    token = config.BOT_TOKEN
    if token == "YOUR_BOT_TOKEN_HERE":
        print("Error: Please set BOT_TOKEN in environment variables")
    else:
        bot.run(token)