# main.py - Discord bot using standard discord.py
import os
import discord
from discord.ext import commands
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
# Включаем необходимые интенты
intents.message_content = True
intents.dm_messages = True
intents.members = False

# Создание экземпляра бота с использованием standard discord.py
bot = commands.Bot(command_prefix='!', intents=intents)

def is_event_active() -> bool:
    """Проверяет, активен ли ивент в настоящее время."""
    try:
        # Парсим время начала и конца из конфигурации
        start_time = datetime.datetime.fromisoformat(config.EVENT_START_TIME.replace('Z', '+00:00'))
        end_time = datetime.datetime.fromisoformat(config.EVENT_END_TIME.replace('Z', '+00:00'))
        
        # Получаем текущее время в UTC
        current_time = datetime.datetime.now(pytz.UTC)
        
        # Проверяем, находится ли текущее время в промежутке ивента
        return start_time <= current_time <= end_time
    except Exception:
        # В случае ошибки парсинга считаем ивент неактивным
        return False

def format_event_dates() -> str:
    """Форматирует даты начала и конца ивента для отображения."""
    try:
        start_time = datetime.datetime.fromisoformat(config.EVENT_START_TIME.replace('Z', '+00:00'))
        end_time = datetime.datetime.fromisoformat(config.EVENT_END_TIME.replace('Z', '+00:00'))
        
        # Форматируем даты
        start_str = start_time.strftime("%d.%m.%Y в %H:%M")
        end_str = end_time.strftime("%d.%m.%Y в %H:%M")
        
        return f"{start_str} до {end_str}"
    except Exception:
        return "даты уточняются"

class RegistrationModal(discord.ui.Modal, title='Регистрация на ивент'):
    """Модальное окно для регистрации на ивент."""
    
    static_id = discord.ui.TextInput(
        label='Ваш StaticID',
        placeholder='Введите ваш StaticID',
        required=True,
        max_length=50
    )
    
    nickname = discord.ui.TextInput(
        label='Ваш игровой Nickname',
        placeholder='Введите ваш игровой никнейм',
        required=True,
        max_length=50
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Обработка отправки формы регистрации."""
        discord_id = interaction.user.id
        static_id_value = self.static_id.value.strip()
        nickname_value = self.nickname.value.strip()
        
        # Попытка регистрации в базе данных
        if database.register_player(discord_id, static_id_value, nickname_value):
            # Успешная регистрация
            await interaction.response.send_message("✅ Регистрация успешна! Проверьте личные сообщения.", ephemeral=True)
            
            # Отправляем приветственное сообщение в ЛС
            try:
                embed = discord.Embed(
                    title="***Добро пожаловать на ивент!***",
                    description="Вы успешно зарегистрированы! Теперь всё взаимодействие происходит здесь, в личных сообщениях со мной.",
                    color=config.RASPBERRY_COLOR
                )
                
                # Добавляем поля с правилами
                embed.add_field(
                    name="***Правила участия:***",
                    value=(
                        "• Просто отправляйте скриншоты найденных локаций мне в этот чат.\n"
                        "• На скриншоте обязательно должен быть виден ваш игровой HUD.\n"
                        "• С каждой уникальной локации принимается только один скриншот.\n"
                        "• Жульничество, передача скриншотов или обман = полная дисквалификация и обнуление всего вашего прогресса."
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="***Сроки проведения:***",
                    value=f"Скриншоты принимаются с {format_event_dates()}.",
                    inline=False
                )
                
                embed.set_footer(text="Удачи в поисках!")
                
                await interaction.user.send(embed=embed)
            except discord.Forbidden:
                # Если не удается отправить ЛС
                await interaction.followup.send("⚠️ Не удалось отправить вам ЛС. Убедитесь, что ЛС открыты.", ephemeral=True)
        else:
            # Игрок уже зарегистрирован
            await interaction.response.send_message("❌ Вы уже зарегистрированы на этот ивент!", ephemeral=True)

class RegistrationView(discord.ui.View):
    """Вид с кнопкой для регистрации."""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='📝 Регистрация', style=discord.ButtonStyle.primary)
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Кнопка для начала регистрации."""
        # Проверяем, зарегистрирован ли уже пользователь
        player = database.get_player(interaction.user.id)
        if player:
            await interaction.response.send_message("❌ Вы уже зарегистрированы на этот ивент!", ephemeral=True)
            return
        
        # Показываем модальное окно регистрации
        modal = RegistrationModal()
        await interaction.response.send_modal(modal)

@bot.event
async def on_ready():
    """Событие готовности бота."""
    print(f'{bot.user} подключен к Discord!')
    
    # Инициализация базы данных
    database.setup_database()
    print("База данных инициализирована.")
    
    # Синхронизируем слэш-команды
    try:
        synced = await bot.tree.sync()
        print(f"Синхронизировано {len(synced)} слэш-команд")
    except Exception as e:
        print(f"Ошибка синхронизации команд: {e}")

@bot.tree.command(name='start', description='Регистрация на ивент поиска локаций')
async def start_registration(interaction: discord.Interaction):
    """Слэш-команда для начала регистрации на ивент."""
    if interaction.guild and interaction.guild.id != config.GUILD_ID:
        await interaction.response.send_message("❌ Команда недоступна на этом сервере.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="***Ивент поиска локаций***",
        description="Нажмите кнопку ниже для регистрации на ивент!",
        color=config.RASPBERRY_COLOR
    )
    
    view = RegistrationView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.event
async def on_message(message):
    """Обработка сообщений в личных сообщениях (прием скриншотов)."""
    
    # Игнорируем сообщения не в ЛС или от самого бота
    if message.guild is not None or message.author == bot.user:
        # Обрабатываем команды
        await bot.process_commands(message)
        return
    
    # Проверяем, зарегистрирован ли пользователь
    player = database.get_player(message.author.id)
    if not player:
        return  # Игнорируем незарегистрированных пользователей
    
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
        return  # Не отвечаем, чтобы избежать спама
    
    # Проверяем, что вложение является изображением
    valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
    screenshot_found = False
    
    for attachment in message.attachments:
        if any(attachment.filename.lower().endswith(ext) for ext in valid_extensions):
            # Добавляем скриншот в базу данных
            if database.add_submission(message.author.id, attachment.url):
                screenshot_found = True
                break
    
    if screenshot_found:
        await message.reply("✅ Скриншот принят!")

async def has_admin_permissions(interaction: discord.Interaction) -> bool:
    """Проверка прав администратора на сервере."""
    if not interaction.guild or interaction.guild.id != config.GUILD_ID:
        return False
    
    # Получаем участника через взаимодействие
    member = interaction.user
    if not hasattr(member, 'guild_permissions'):
        # Если это User, а не Member, получаем Member объект
        member = await interaction.guild.fetch_member(interaction.user.id)
    
    # Проверяем права администратора
    return member.guild_permissions.administrator

class PlayerListView(discord.ui.View):
    """Выпадающее меню для выбора игрока из списка."""
    
    def __init__(self, players_data):
        super().__init__(timeout=300)
        self.players_data = players_data
        
        # Создаем выпадающий список с игроками
        options = []
        for player in players_data[:25]:  # Discord ограничивает до 25 опций
            discord_id, nickname, static_id, screenshot_count, is_disqualified = player
            user = bot.get_user(discord_id)
            user_tag = user.display_name if user else f"ID:{discord_id}"
            
            status = "❌ ДИСКВ." if is_disqualified else f"📸 {screenshot_count}"
            
            options.append(discord.SelectOption(
                label=f"{user_tag} ({nickname})",
                description=f"StaticID: {static_id} | {status}",
                value=str(discord_id)
            ))
        
        if options:
            self.select_player.options = options
        else:
            # Если нет игроков, отключаем селект
            self.select_player.disabled = True
            self.select_player.placeholder = "Нет зарегистрированных игроков"
    
    @discord.ui.select(placeholder="Выберите игрока для просмотра профиля...")
    async def select_player(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Обработка выбора игрока."""
        if not await has_admin_permissions(interaction):
            await interaction.response.send_message("❌ У вас нет прав для использования этой функции.", ephemeral=True)
            return
            
        discord_id = int(select.values[0])
        user = bot.get_user(discord_id)
        
        if user:
            # Получаем данные игрока
            player = database.get_player(discord_id)
            screenshots = database.get_player_submissions(discord_id)
            
            if player:
                embed = discord.Embed(
                    title=f"👤 Профиль игрока",
                    color=config.RASPBERRY_COLOR
                )
                
                # Основная информация
                status = "❌ Дисквалифицирован" if player['is_disqualified'] else "✅ Активен"
                embed.add_field(
                    name="Основная информация",
                    value=f"**Пользователь:** {user.mention}\n**Никнейм:** {player['nickname']}\n**StaticID:** {player['static_id']}\n**Статус:** {status}",
                    inline=False
                )
                
                # Статистика скриншотов
                valid_screenshots = len([s for s in screenshots if s['is_valid']])
                embed.add_field(
                    name="📸 Статистика скриншотов",
                    value=f"Всего отправлено: **{len(screenshots)}**\nВалидных: **{valid_screenshots}**",
                    inline=True
                )
                
                # Дата регистрации
                embed.add_field(
                    name="📅 Регистрация",
                    value=f"<t:{int(player['registration_time'])}:F>",
                    inline=True
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Игрок не найден в базе данных.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Пользователь не найден.", ephemeral=True)

@bot.tree.command(name='admin_stats', description='Статистика ивента и список всех участников')
async def admin_stats(interaction: discord.Interaction):
    """Слэш-команда для получения статистики ивента."""
    if not await has_admin_permissions(interaction):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    # Получаем полный список игроков с дополнительной информацией
    conn = sqlite3.connect('event_data.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.discord_id, p.nickname, p.static_id, 
               COUNT(CASE WHEN s.is_valid = 1 THEN 1 END) as screenshot_count,
               p.is_disqualified
        FROM players p
        LEFT JOIN submissions s ON p.discord_id = s.player_id
        GROUP BY p.discord_id, p.nickname, p.static_id, p.is_disqualified
        ORDER BY screenshot_count DESC, p.nickname ASC
    """)
    
    players_data = cursor.fetchall()
    total_players = len(players_data)
    conn.close()
    
    embed = discord.Embed(
        title="📊 Статистика ивента",
        color=config.RASPBERRY_COLOR
    )
    
    # Общая информация
    active_players = len([p for p in players_data if not p[4]])  # not is_disqualified
    disqualified_players = total_players - active_players
    
    embed.add_field(
        name="Общая статистика",
        value=f"Всего участников: **{total_players}**\nАктивных: **{active_players}**\nДисквалифицированных: **{disqualified_players}**\nАктивный период: {format_event_dates()}",
        inline=False
    )
    
    # Топ 10 участников
    if players_data:
        top_text = ""
        for i, (discord_id, nickname, static_id, screenshot_count, is_disqualified) in enumerate(players_data[:10], 1):
            user = bot.get_user(discord_id)
            user_display = user.display_name if user else f"ID:{discord_id}"
            status = " ❌" if is_disqualified else ""
            top_text += f"**{i}.** {user_display} ({nickname}) - **{screenshot_count}** скриншотов{status}\n"
        
        embed.add_field(
            name="🏆 Топ 10 участников",
            value=top_text,
            inline=False
        )
    else:
        embed.add_field(
            name="🏆 Топ участников",
            value="Пока нет участников",
            inline=False
        )
    
    # Добавляем информацию о выпадающем меню
    if players_data:
        embed.add_field(
            name="👥 Список участников",
            value="Используйте выпадающее меню ниже для просмотра профиля любого участника",
            inline=False
        )
    
    if players_data:
        view = PlayerListView(players_data)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ScreenshotPaginator(discord.ui.View):
    """Пагинатор для просмотра скриншотов игрока."""
    
    def __init__(self, screenshots, player_info, per_page=10):
        super().__init__(timeout=300)
        self.screenshots = screenshots
        self.player_info = player_info
        self.per_page = per_page
        self.current_page = 0
        self.max_page = max(0, (len(screenshots) - 1) // per_page)
        
        # Обновляем состояние кнопок
        self.update_buttons()
    
    def update_buttons(self):
        """Обновляет состояние кнопок пагинации."""
        self.prev_button.disabled = self.current_page <= 0
        self.next_button.disabled = self.current_page >= self.max_page
    
    def get_current_embed(self):
        """Создает Embed для текущей страницы."""
        embed = discord.Embed(
            title=f"***Профиль игрока: {self.player_info['nickname']}***",
            color=config.RASPBERRY_COLOR
        )
        
        embed.add_field(name="**StaticID**", value=self.player_info['static_id'], inline=True)
        embed.add_field(name="**Дисквалифицирован**", value="Да" if self.player_info['is_disqualified'] else "Нет", inline=True)
        embed.add_field(name="**Всего скриншотов**", value=str(len(self.screenshots)), inline=True)
        
        # Получаем скриншоты для текущей страницы
        start_idx = self.current_page * self.per_page
        end_idx = min(start_idx + self.per_page, len(self.screenshots))
        current_screenshots = self.screenshots[start_idx:end_idx]
        
        if current_screenshots:
            screenshot_links = []
            for i, screenshot in enumerate(current_screenshots, start_idx + 1):
                status = "✅" if screenshot['is_valid'] else "❌"
                screenshot_links.append(f"{status} [{i}. Скриншот]({screenshot['screenshot_url']})")
            
            embed.add_field(
                name=f"**Скриншоты (страница {self.current_page + 1}/{self.max_page + 1})**",
                value="\n".join(screenshot_links),
                inline=False
            )
        else:
            embed.add_field(
                name="**Скриншоты**",
                value="Нет скриншотов",
                inline=False
            )
        
        return embed
    
    @discord.ui.button(label="◀ Назад", style=discord.ButtonStyle.secondary)
    async def prev_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Кнопка для перехода на предыдущую страницу."""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_current_embed(), view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="Вперед ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Кнопка для перехода на следующую страницу."""
        if self.current_page < self.max_page:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_current_embed(), view=self)
        else:
            await interaction.response.defer()

@bot.tree.command(name='admin_profile', description='Просмотр профиля конкретного игрока')
async def admin_profile(interaction: discord.Interaction, user: discord.Member):
    """Слэш-команда для просмотра профиля игрока."""
    if not await has_admin_permissions(interaction):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    # Получаем данные игрока
    player = database.get_player(user.id)
    if not player:
        await interaction.response.send_message("❌ Этот пользователь не зарегистрирован на ивенте.", ephemeral=True)
        return
    
    # Получаем все скриншоты игрока
    screenshots = database.get_player_submissions(user.id)
    
    # Если скриншотов много, используем пагинацию
    if len(screenshots) > 10:
        paginator = ScreenshotPaginator(screenshots, player)
        await interaction.response.send_message(embed=paginator.get_current_embed(), view=paginator, ephemeral=True)
    else:
        # Создаем простой Embed без пагинации
        embed = discord.Embed(
            title=f"👤 Профиль игрока: {player['nickname']}",
            color=config.RASPBERRY_COLOR
        )
        
        status = "❌ Дисквалифицирован" if player['is_disqualified'] else "✅ Активен"
        embed.add_field(
            name="Основная информация",
            value=f"**Пользователь:** {user.mention}\n**Никнейм:** {player['nickname']}\n**StaticID:** {player['static_id']}\n**Статус:** {status}",
            inline=False
        )
        
        valid_screenshots = len([s for s in screenshots if s['is_valid']])
        embed.add_field(
            name="📸 Статистика скриншотов",
            value=f"Всего отправлено: **{len(screenshots)}**\nВалидных: **{valid_screenshots}**",
            inline=True
        )
        
        embed.add_field(
            name="📅 Регистрация",
            value=f"<t:{int(player['registration_time'])}:F>",
            inline=True
        )
        
        if screenshots:
            screenshot_links = []
            for i, screenshot in enumerate(screenshots, 1):
                status = "✅" if screenshot['is_valid'] else "❌"
                screenshot_links.append(f"{status} [{i}. Скриншот]({screenshot['screenshot_url']})")
            
            embed.add_field(
                name="🖼️ Скриншоты",
                value="\n".join(screenshot_links),
                inline=False
            )
        else:
            embed.add_field(
                name="🖼️ Скриншоты",
                value="Нет скриншотов",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='admin_disqualify', description='Дисквалификация игрока с ивента')
async def admin_disqualify(interaction: discord.Interaction, user: discord.Member):
    """Слэш-команда для дисквалификации игрока."""
    if not await has_admin_permissions(interaction):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    # Проверяем, зарегистрирован ли игрок
    player = database.get_player(user.id)
    if not player:
        await interaction.response.send_message("❌ Этот пользователь не зарегистрирован на ивенте.", ephemeral=True)
        return
    
    # Проверяем, не дисквалифицирован ли уже
    if player['is_disqualified']:
        await interaction.response.send_message("❌ Этот игрок уже дисквалифицирован.", ephemeral=True)
        return
    
    # Дисквалифицируем игрока
    if database.disqualify_player(user.id):
        await interaction.response.send_message(f"✅ Игрок {user.mention} ({player['nickname']}) успешно дисквалифицирован.", ephemeral=True)
        
        # Пытаемся отправить уведомление игроку в ЛС
        try:
            embed = discord.Embed(
                title="🚫 Уведомление о дисквалификации",
                description="К сожалению, вы были дисквалифицированы с ивента поиска локаций.",
                color=config.RASPBERRY_COLOR
            )
            embed.add_field(
                name="Причина",
                value="Нарушение правил ивента",
                inline=False
            )
            embed.set_footer(text="При возникновении вопросов обратитесь к администрации.")
            
            await user.send(embed=embed)
        except discord.Forbidden:
            await interaction.followup.send("⚠️ Не удалось отправить уведомление игроку в ЛС.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Произошла ошибка при дисквалификации игрока.", ephemeral=True)

# Обработка ошибок команд
@bot.event
async def on_command_error(ctx, error):
    """Обработчик ошибок команд."""
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ У вас нет прав для выполнения этой команды.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Пользователь не найден.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Не хватает обязательных аргументов для команды.")
    else:
        print(f"Ошибка команды: {error}")

# Запуск бота
if __name__ == "__main__":
    token = config.BOT_TOKEN
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        print("❌ Ошибка: Не указан токен бота. Добавьте BOT_TOKEN в переменные окружения.")
    else:
        bot.run(token)
