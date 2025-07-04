import os
import discord
from discord.ext import commands
from discord import app_commands
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

# Создание экземпляра бота для discord.py
bot = commands.Bot(command_prefix='!', intents=intents)

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

# Модальное окно для регистрации (discord.py версия)
class RegistrationModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title='Регистрация на ивент')
        
        self.static_id = discord.ui.TextInput(
            label='Ваш StaticID',
            placeholder='Введите ваш StaticID',
            required=True,
            max_length=50
        )
        self.add_item(self.static_id)
        
        self.nickname = discord.ui.TextInput(
            label='Ваш игровой Nickname',
            placeholder='Введите ваш игровой никнейм',
            required=True,
            max_length=50
        )
        self.add_item(self.nickname)

    async def on_submit(self, interaction: discord.Interaction):
        """Обработка отправки формы регистрации."""
        await interaction.response.defer(ephemeral=True)
        
        # Проверяем, активен ли ивент
        if not is_event_active():
            embed = discord.Embed(
                title="❌ Регистрация недоступна",
                description=f"Ивент не активен.\n\nИвент проходит: {format_event_dates()}",
                color=config.RASPBERRY_COLOR
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Пытаемся зарегистрировать игрока
        success = database.register_player(
            discord_id=interaction.user.id,
            static_id=self.static_id.value.strip(),
            nickname=self.nickname.value.strip()
        )
        
        if success:
            embed = discord.Embed(
                title="✅ Регистрация успешна!",
                description=f"Добро пожаловать на ивент!\n\n"
                           f"**StaticID:** {self.static_id.value}\n"
                           f"**Nickname:** {self.nickname.value}\n\n"
                           f"Теперь вы можете отправлять скриншоты в личные сообщения боту.",
                color=config.RASPBERRY_COLOR
            )
            
            # Отправляем личное сообщение с подтверждением регистрации
            try:
                dm_embed = discord.Embed(
                    title="🎮 Добро пожаловать на ивент!",
                    description=f"Вы успешно зарегистрированы! Теперь всё взаимодействие происходит здесь, в личных сообщениях со мной.\n\n"
                               f"**Правила участия:**\n"
                               f"• Просто отправляйте скриншоты найденных локаций мне в этот чат.\n"
                               f"• На скриншоте обязательно должен быть виден ваш игровой HUD.\n"
                               f"• С каждой уникальной локации принимается только один скриншот.\n"
                               f"• Жульничество, передача скриншотов или обман = полная дисквалификация и обнуление всего вашего прогресса.\n\n"
                               f"**Сроки проведения:**\n"
                               f"Скриншоты принимаются {format_event_dates()}.\n\n"
                               f"**Удачи в поисках!**",
                    color=config.RASPBERRY_COLOR
                )
                await interaction.user.send(embed=dm_embed)
                print(f"✅ Уведомление о регистрации отправлено пользователю {interaction.user}")
            except discord.Forbidden:
                print(f"❌ Не удалось отправить DM пользователю {interaction.user.id} - закрыты личные сообщения")
            except Exception as e:
                print(f"❌ Ошибка при отправке DM регистрации: {e}")
        else:
            embed = discord.Embed(
                title="❌ Ошибка регистрации",
                description="Вы уже зарегистрированы на этот ивент.",
                color=config.RASPBERRY_COLOR
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

# Вид с кнопкой регистрации
class RegistrationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Регистрация', style=discord.ButtonStyle.primary, emoji='📝')
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Кнопка для начала регистрации."""
        modal = RegistrationModal()
        await interaction.response.send_modal(modal)

# Выпадающий список для выбора скриншотов
class ScreenshotSelect(discord.ui.Select):
    def __init__(self, submissions, player_info):
        self.submissions = submissions
        self.player_info = player_info
        
        options = []
        for i, submission in enumerate(submissions[:25]):  # Discord ограничивает до 25 опций
            status_emoji = "✅" if submission.get('is_approved') == 1 else "❌" if submission.get('is_approved') == 0 else "⏳"
            screenshot_number = database.get_player_screenshot_number(player_info['discord_id'], submission['submission_id'])
            options.append(discord.SelectOption(
                label=f"Скриншот #{screenshot_number}",
                description=f"{status_emoji} Отправлен: {submission['submission_time'][:16]}",
                value=str(submission['submission_id'])
            ))
        
        super().__init__(placeholder="Выберите скриншот для модерации...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        submission_id = int(self.values[0])
        submission = database.get_submission_by_id(submission_id)
        
        if not submission:
            await interaction.response.send_message("❌ Скриншот не найден.", ephemeral=True)
            return
        
        screenshot_number = database.get_player_screenshot_number(self.player_info['discord_id'], submission_id)
        status_text = "✅ Одобрен" if submission.get('is_approved') == 1 else "❌ Отклонен" if submission.get('is_approved') == 0 else "⏳ На модерации"
        
        embed = discord.Embed(
            title=f"Скриншот #{screenshot_number} - {self.player_info['nickname']}",
            description=f"**Игрок:** @{get_user_tag(self.player_info['discord_id'])}\n"
                       f"**StaticID:** {self.player_info['static_id']}\n"
                       f"**Время отправки:** {submission['submission_time']}\n"
                       f"**Статус:** {status_text}",
            color=config.RASPBERRY_COLOR
        )
        embed.set_image(url=submission['screenshot_url'])
        
        view = ScreenshotModerationView(submission_id, submission.get('is_approved'))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# Модальное окно для причины отклонения
class RejectReasonModal(discord.ui.Modal):
    def __init__(self, submission_id, view):
        super().__init__(title='Причина отклонения')
        self.submission_id = submission_id
        self.parent_view = view
        
        self.reason = discord.ui.TextInput(
            label='Причина отклонения скриншота',
            placeholder='Введите причину отклонения...',
            required=True,
            max_length=500,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        success = database.reject_screenshot(self.submission_id)
        
        if success:
            submission = database.get_submission_by_id(self.submission_id)
            player = database.get_player(submission['discord_id'])
            
            # Уведомляем игрока
            try:
                print(f"🔍 Поиск пользователя с ID: {submission['discord_id']} для отклонения")
                user = bot.get_user(submission['discord_id'])
                if user:
                    print(f"✅ Пользователь найден: {user.name}")
                    screenshot_number = database.get_player_screenshot_number(submission['discord_id'], self.submission_id)
                    embed = discord.Embed(
                        title="⚠️ Скриншот отклонен",
                        description=f"К сожалению, ваш скриншот #{screenshot_number} не прошел модерацию.\n\n"
                                   f"❌ **Статус:** Отклонено\n"
                                   f"📝 **Причина отклонения:**\n{self.reason.value}\n\n"
                                   f"💡 **Что делать:**\n"
                                   f"Изучите причину отклонения и отправьте новый скриншот, учитывая указанные замечания.\n\n"
                                   f"**Удачи в следующих попытках!**",
                        color=config.RASPBERRY_COLOR
                    )
                    embed.set_image(url=submission['screenshot_url'])
                    embed.set_footer(text="Не расстраивайтесь! Попробуйте еще раз с учетом замечаний.")
                    print(f"📨 Отправка DM об отклонении пользователю {user.name}...")
                    await user.send(embed=embed)
                    print(f"✅ Уведомление об отклонении отправлено пользователю {user.name}")
                else:
                    print(f"❌ Пользователь с ID {submission['discord_id']} не найден через bot.get_user()")
                    # Попробуем найти через fetch_user
                    try:
                        user = await bot.fetch_user(submission['discord_id'])
                        print(f"✅ Пользователь найден через fetch_user: {user.name}")
                        screenshot_number = database.get_player_screenshot_number(submission['discord_id'], self.submission_id)
                        embed = discord.Embed(
                            title="⚠️ Скриншот отклонен",
                            description=f"К сожалению, ваш скриншот #{screenshot_number} не прошел модерацию.\n\n"
                                       f"❌ **Статус:** Отклонено\n"
                                       f"📝 **Причина отклонения:**\n{self.reason.value}\n\n"
                                       f"💡 **Что делать:**\n"
                                       f"Изучите причину отклонения и отправьте новый скриншот, учитывая указанные замечания.\n\n"
                                       f"**Удачи в следующих попытках!**",
                            color=config.RASPBERRY_COLOR
                        )
                        embed.set_image(url=submission['screenshot_url'])
                        embed.set_footer(text="Не расстраивайтесь! Попробуйте еще раз с учетом замечаний.")
                        print(f"📨 Отправка DM об отклонении пользователю {user.name} через fetch_user...")
                        await user.send(embed=embed)
                        print(f"✅ Уведомление об отклонении отправлено пользователю {user.name}")
                    except Exception as fetch_e:
                        print(f"❌ Не удалось найти пользователя через fetch_user: {fetch_e}")
            except discord.Forbidden:
                print(f"❌ Не удалось отправить DM пользователю {submission['discord_id']} - закрыты личные сообщения")
            except discord.HTTPException as e:
                print(f"❌ Ошибка HTTP при отправке DM: {e}")
            except Exception as e:
                print(f"❌ Неожиданная ошибка при отправке DM: {e}")
            
            await interaction.response.send_message("✅ Скриншот отклонен, игрок уведомлен.", ephemeral=True)
            await self.parent_view.update_parent_stats_if_needed(interaction)
        else:
            await interaction.response.send_message("❌ Ошибка при отклонении скриншота.", ephemeral=True)

# Вид для модерации скриншотов
class ScreenshotModerationView(discord.ui.View):
    def __init__(self, submission_id, current_status):
        super().__init__(timeout=300)
        self.submission_id = submission_id
        self.current_status = current_status

    async def update_parent_stats_if_needed(self, interaction):
        """Обновляет статистику в родительском сообщении admin_stats если возможно"""
        try:
            # Попытка найти сообщение со статистикой для обновления
            pass
        except:
            pass

    @discord.ui.button(label='✅ Одобрить', style=discord.ButtonStyle.success)
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = database.approve_screenshot(self.submission_id)
        
        if success:
            submission = database.get_submission_by_id(self.submission_id)
            player = database.get_player(submission['discord_id'])
            
            # Уведомляем игрока
            try:
                print(f"🔍 Поиск пользователя с ID: {submission['discord_id']}")
                user = bot.get_user(submission['discord_id'])
                if user:
                    print(f"✅ Пользователь найден: {user.name}")
                    screenshot_number = database.get_player_screenshot_number(submission['discord_id'], self.submission_id)
                    embed = discord.Embed(
                        title="🎉 Скриншот одобрен!",
                        description=f"**Отличная работа!** Ваш скриншот #{screenshot_number} успешно прошел модерацию.\n\n"
                                   f"✅ **Статус:** Одобрено\n"
                                   f"📊 **Прогресс:** Скриншот засчитан в вашу статистику\n\n"
                                   f"**Продолжайте в том же духе!**",
                        color=config.RASPBERRY_COLOR
                    )
                    embed.set_image(url=submission['screenshot_url'])
                    embed.set_footer(text="Спасибо за участие в ивенте!")
                    print(f"📨 Отправка DM пользователю {user.name}...")
                    await user.send(embed=embed)
                    print(f"✅ Уведомление об одобрении отправлено пользователю {user.name}")
                else:
                    print(f"❌ Пользователь с ID {submission['discord_id']} не найден через bot.get_user()")
                    # Попробуем найти через fetch_user
                    try:
                        user = await bot.fetch_user(submission['discord_id'])
                        print(f"✅ Пользователь найден через fetch_user: {user.name}")
                        screenshot_number = database.get_player_screenshot_number(submission['discord_id'], self.submission_id)
                        embed = discord.Embed(
                            title="🎉 Скриншот одобрен!",
                            description=f"**Отличная работа!** Ваш скриншот #{screenshot_number} успешно прошел модерацию.\n\n"
                                       f"✅ **Статус:** Одобрено\n"
                                       f"📊 **Прогресс:** Скриншот засчитан в вашу статистику\n\n"
                                       f"**Продолжайте в том же духе!**",
                            color=config.RASPBERRY_COLOR
                        )
                        embed.set_image(url=submission['screenshot_url'])
                        embed.set_footer(text="Спасибо за участие в ивенте!")
                        print(f"📨 Отправка DM пользователю {user.name} через fetch_user...")
                        await user.send(embed=embed)
                        print(f"✅ Уведомление об одобрении отправлено пользователю {user.name}")
                    except Exception as fetch_e:
                        print(f"❌ Не удалось найти пользователя через fetch_user: {fetch_e}")
            except discord.Forbidden:
                print(f"❌ Не удалось отправить DM пользователю {submission['discord_id']} - закрыты личные сообщения")
            except discord.HTTPException as e:
                print(f"❌ Ошибка HTTP при отправке DM: {e}")
            except Exception as e:
                print(f"❌ Неожиданная ошибка при отправке DM: {e}")
            
            await interaction.response.send_message("✅ Скриншот одобрен, игрок уведомлен.", ephemeral=True)
            await self.update_parent_stats_if_needed(interaction)
        else:
            await interaction.response.send_message("❌ Ошибка при одобрении скриншота.", ephemeral=True)

    @discord.ui.button(label='❌ Отклонить', style=discord.ButtonStyle.danger)
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RejectReasonModal(self.submission_id, self)
        await interaction.response.send_modal(modal)

# Выпадающий список игроков с пагинацией
class PlayerSelect(discord.ui.Select):
    def __init__(self, players_data, page=0):
        self.players_data = players_data
        self.page = page
        self.per_page = 25
        
        start_idx = page * self.per_page
        end_idx = start_idx + self.per_page
        current_players = players_data[start_idx:end_idx]
        
        options = []
        for player in current_players:
            discord_id, nickname, total_screenshots, approved_count = player
            user_tag = get_user_tag(discord_id)
            
            # Получаем реальную статистику для каждого игрока
            submissions = database.get_player_submissions(discord_id)
            approved_count_real = sum(1 for s in submissions if s.get('is_approved') == 1)
            rejected_count_real = sum(1 for s in submissions if s.get('is_approved') == 0)
            pending_count_real = sum(1 for s in submissions if s.get('is_approved') is None)
            
            options.append(discord.SelectOption(
                label=f"{user_tag} - {nickname}",
                description=f"✅{approved_count_real} ❌{rejected_count_real} ⏳{pending_count_real}",
                value=str(discord_id)
            ))
        
        super().__init__(placeholder=f"Выберите игрока (стр. {page+1})...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        discord_id = int(self.values[0])
        player = database.get_player(discord_id)
        submissions = database.get_player_submissions(discord_id)
        
        if not player:
            await interaction.response.send_message("❌ Игрок не найден.", ephemeral=True)
            return
        
        user_tag = get_user_tag(discord_id)
        approved_count = sum(1 for s in submissions if s.get('is_approved') == 1)
        rejected_count = sum(1 for s in submissions if s.get('is_approved') == 0)
        pending_count = sum(1 for s in submissions if s.get('is_approved') is None)
        
        embed = discord.Embed(
            title=f"Профиль игрока: {player['nickname']}",
            description=f"**Discord:** {user_tag}\n"
                       f"**StaticID:** {player['static_id']}\n"
                       f"**Дата регистрации:** {player['registration_time'][:16]}\n\n"
                       f"**Статистика скриншотов:**\n"
                       f"✅ Одобрено: {approved_count}\n"
                       f"❌ Отклонено: {rejected_count}\n"
                       f"⏳ На модерации: {pending_count}\n"
                       f"📊 Всего: {len(submissions)}",
            color=config.RASPBERRY_COLOR
        )
        
        view = PlayerProfileView(submissions, player)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# Вид профиля игрока
class PlayerProfileView(discord.ui.View):
    def __init__(self, submissions, player_info):
        super().__init__(timeout=300)
        self.add_item(ScreenshotSelect(submissions, player_info))

# Основной вид со списком игроков
class PlayerListView(discord.ui.View):
    def __init__(self, players_data):
        super().__init__(timeout=300)
        self.players_data = players_data
        self.current_page = 0
        self.max_page = (len(players_data) - 1) // 25
        
        self.add_item(PlayerSelect(players_data, self.current_page))
        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Обновляет состояние кнопок навигации"""
        # Очищаем существующие кнопки навигации
        for item in self.children[:]:
            if isinstance(item, discord.ui.Button):
                self.remove_item(item)
        
        # Добавляем кнопки навигации если нужно
        if self.max_page > 0:
            prev_button = discord.ui.Button(
                label='◀️ Назад',
                style=discord.ButtonStyle.secondary,
                disabled=(self.current_page == 0)
            )
            prev_button.callback = self.prev_page
            self.add_item(prev_button)
            
            next_button = discord.ui.Button(
                label='Вперед ▶️',
                style=discord.ButtonStyle.secondary,
                disabled=(self.current_page == self.max_page)
            )
            next_button.callback = self.next_page
            self.add_item(next_button)

    async def prev_page(self, interaction: discord.Interaction):
        """Переход на предыдущую страницу"""
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_page(interaction)

    async def next_page(self, interaction: discord.Interaction):
        """Переход на следующую страницу"""
        if self.current_page < self.max_page:
            self.current_page += 1
            await self.update_page(interaction)

    async def update_page(self, interaction: discord.Interaction):
        """Обновляет страницу с новым списком игроков"""
        # Обновляем выпадающий список
        for item in self.children[:]:
            if isinstance(item, PlayerSelect):
                self.remove_item(item)
        
        self.add_item(PlayerSelect(self.players_data, self.current_page))
        self.update_navigation_buttons()
        
        await interaction.response.edit_message(view=self)

@bot.event
async def on_ready():
    """Событие готовности бота."""
    print(f"{bot.user} подключен к Discord!")
    database.setup_database()
    print("База данных инициализирована.")
    
    # Синхронизируем слэш-команды с Discord
    try:
        if config.GUILD_ID:
            guild = discord.Object(id=config.GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"Команды синхронизированы для сервера {config.GUILD_ID}")
        else:
            await bot.tree.sync()
            print("Команды синхронизированы глобально")
    except Exception as e:
        print(f"Ошибка синхронизации команд: {e}")

@bot.tree.command(name="start", description="Начать регистрацию на ивент")
async def start_registration(interaction: discord.Interaction):
    """Команда для начала регистрации на ивент."""
    embed = discord.Embed(
        title="🎮 Добро пожаловать на ивент!",
        description=f"**Период проведения:** {format_event_dates()}\n\n"
                   f"Для участия в ивенте нажмите кнопку ниже и заполните форму регистрации.",
        color=config.RASPBERRY_COLOR
    )
    
    view = RegistrationView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="test_dm", description="Тест отправки личного сообщения")
async def test_dm(interaction: discord.Interaction):
    """Тестовая команда для проверки отправки DM."""
    try:
        embed = discord.Embed(
            title="🧪 Тест личного сообщения",
            description="Это тестовое сообщение для проверки работы личных сообщений.",
            color=config.RASPBERRY_COLOR
        )
        await interaction.user.send(embed=embed)
        await interaction.response.send_message("✅ Тестовое сообщение отправлено в ваши личные сообщения!", ephemeral=True)
        print(f"✅ Тестовое DM отправлено пользователю {interaction.user}")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Не удалось отправить личное сообщение. У вас закрыты DM от участников сервера.", ephemeral=True)
        print(f"❌ DM заблокированы для пользователя {interaction.user.id}")
    except discord.HTTPException as e:
        await interaction.response.send_message(f"❌ Ошибка HTTP при отправке сообщения: {e}", ephemeral=True)
        print(f"❌ Ошибка HTTP при отправке DM: {e}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Неожиданная ошибка: {e}", ephemeral=True)
        print(f"❌ Неожиданная ошибка при отправке DM: {e}")

@bot.event
async def on_message(message):
    """Обработка сообщений в личных сообщениях (прием скриншотов)."""
    # Игнорируем сообщения от ботов
    if message.author.bot:
        return
    
    # Обрабатываем только личные сообщения
    if not isinstance(message.channel, discord.DMChannel):
        await bot.process_commands(message)
        return
    
    # Проверяем, зарегистрирован ли игрок
    player = database.get_player(message.author.id)
    if not player:
        embed = discord.Embed(
            title="❌ Не зарегистрирован",
            description="Вы не зарегистрированы на ивент. Сначала зарегистрируйтесь на сервере командой `/start`.",
            color=config.RASPBERRY_COLOR
        )
        await message.channel.send(embed=embed)
        return
    
    # Проверяем, не дисквалифицирован ли игрок
    if database.is_player_disqualified(message.author.id):
        embed = discord.Embed(
            title="❌ Дисквалификация",
            description="Вы дисквалифицированы и не можете отправлять скриншоты.",
            color=config.RASPBERRY_COLOR
        )
        await message.channel.send(embed=embed)
        return
    
    # Проверяем, активен ли ивент
    if not is_event_active():
        embed = discord.Embed(
            title="❌ Ивент неактивен",
            description=f"Ивент не активен в данный момент.\n\nИвент проходит: {format_event_dates()}",
            color=config.RASPBERRY_COLOR
        )
        await message.channel.send(embed=embed)
        return
    
    # Проверяем наличие вложений (скриншотов)
    if not message.attachments:
        embed = discord.Embed(
            title="📷 Отправьте скриншот",
            description="Прикрепите скриншот к сообщению для участия в ивенте.",
            color=config.RASPBERRY_COLOR
        )
        await message.channel.send(embed=embed)
        return
    
    # Обрабатываем первое вложение как скриншот
    attachment = message.attachments[0]
    
    # Проверяем, что это изображение
    if not any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
        embed = discord.Embed(
            title="❌ Неверный формат",
            description="Пожалуйста, отправьте изображение (PNG, JPG, JPEG, GIF, WEBP).",
            color=config.RASPBERRY_COLOR
        )
        await message.channel.send(embed=embed)
        return
    
    # Сохраняем скриншот в базу данных
    success = database.add_submission(player['discord_id'], attachment.url)
    
    if success:
        submissions_count = len(database.get_player_submissions(message.author.id))
        embed = discord.Embed(
            title="✅ Скриншот принят на модерацию!",
            description=f"**Скриншот #{submissions_count}** успешно получен и отправлен на проверку.\n\n"
                       f"📋 **Статус:** На модерации ⏳\n"
                       f"🔔 **Уведомления:** Вы получите сообщение о результатах проверки\n\n"
                       f"**Спасибо за участие в ивенте!**",
            color=config.RASPBERRY_COLOR
        )
        embed.set_image(url=attachment.url)
        embed.set_footer(text=f"Игрок: {player['nickname']} | StaticID: {player['static_id']}")
    else:
        embed = discord.Embed(
            title="❌ Ошибка при сохранении",
            description="Произошла ошибка при обработке вашего скриншота. Пожалуйста, попробуйте отправить его еще раз.\n\n"
                       f"Если проблема повторяется, обратитесь к администраторам.",
            color=config.RASPBERRY_COLOR
        )
    
    await message.channel.send(embed=embed)
    await bot.process_commands(message)

async def has_admin_permissions(interaction: discord.Interaction) -> bool:
    """Проверка прав администратора на сервере."""
    if not interaction.guild:
        return False
    
    # Пытаемся получить участника через interaction
    member = interaction.user
    if hasattr(member, 'guild_permissions') and member.guild_permissions:
        return member.guild_permissions.administrator
    
    # Альтернативный способ - получаем участника через guild
    try:
        guild_member = interaction.guild.get_member(interaction.user.id)
        if guild_member:
            return guild_member.guild_permissions.administrator
            
        # Если get_member не работает, используем fetch_member
        guild_member = await interaction.guild.fetch_member(interaction.user.id)
        if guild_member:
            return guild_member.guild_permissions.administrator
    except:
        pass
    
    # Проверяем роли на наличие прав администратора
    try:
        if hasattr(interaction.user, 'roles'):
            for role in interaction.user.roles:
                if role.permissions.administrator:
                    return True
    except:
        pass
    
    return False

@bot.tree.command(name="admin_stats", description="Получить статистику ивента (только для админов)")
async def admin_stats(interaction: discord.Interaction):
    """Команда для получения статистики ивента."""
    # Диагностическая информация
    debug_info = f"User: {interaction.user}\nGuild: {interaction.guild}\n"
    if interaction.guild:
        try:
            member = interaction.guild.get_member(interaction.user.id)
            if member:
                debug_info += f"Member found: {member}\nAdmin perms: {member.guild_permissions.administrator}\n"
                debug_info += f"Roles: {[role.name for role in member.roles]}\n"
            else:
                debug_info += "Member not found with get_member\n"
        except Exception as e:
            debug_info += f"Error getting member: {e}\n"
    
    has_perms = await has_admin_permissions(interaction)
    if not has_perms:
        await interaction.response.send_message(
            f"❌ У вас нет прав для использования этой команды.\n\nДиагностика:\n```{debug_info}```", 
            ephemeral=True
        )
        return
    
    await interaction.response.defer(ephemeral=True)
    
    # Получаем статистику
    total_players = database.get_all_players_stats()
    approved_stats = database.get_approved_screenshots_stats()
    leaderboard = database.get_leaderboard_by_approved()
    
    # Формируем топ-5 игроков
    top_players_text = ""
    for i, (discord_id, nickname, total_screenshots, approved_count) in enumerate(leaderboard[:5], 1):
        user_tag = get_user_tag(discord_id)
        top_players_text += f"{i}. {user_tag} - {nickname} (✅{approved_count})\n"
    
    if not top_players_text:
        top_players_text = "Нет игроков"
    
    embed = discord.Embed(
        title="📊 Статистика ивента",
        description=f"**Всего участников:** {total_players}\n"
                   f"**Период ивента:** {format_event_dates()}\n"
                   f"**Статус:** {'🟢 Активен' if is_event_active() else '🔴 Неактивен'}\n\n"
                   f"**Топ-5 игроков:**\n{top_players_text}",
        color=config.RASPBERRY_COLOR
    )
    
    # Добавляем выпадающий список только если есть игроки
    if leaderboard:
        view = PlayerListView(leaderboard)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    else:
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="admin_profile", description="Просмотреть профиль игрока (только для админов)")
async def admin_profile(interaction: discord.Interaction, user: discord.Member):
    """Команда для просмотра профиля игрока."""
    if not await has_admin_permissions(interaction):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    player = database.get_player(user.id)
    if not player:
        await interaction.followup.send("❌ Пользователь не зарегистрирован на ивент.", ephemeral=True)
        return
    
    submissions = database.get_player_submissions(user.id)
    user_tag = get_user_tag(user.id)
    
    approved_count = sum(1 for s in submissions if s.get('is_approved') == 1)
    rejected_count = sum(1 for s in submissions if s.get('is_approved') == 0)
    pending_count = sum(1 for s in submissions if s.get('is_approved') is None)
    
    embed = discord.Embed(
        title=f"Профиль игрока: {player['nickname']}",
        description=f"**Discord:** {user_tag}\n"
                   f"**StaticID:** {player['static_id']}\n"
                   f"**Дата регистрации:** {player['registration_time'][:16]}\n\n"
                   f"**Статистика скриншотов:**\n"
                   f"✅ Одобрено: {approved_count}\n"
                   f"❌ Отклонено: {rejected_count}\n"
                   f"⏳ На модерации: {pending_count}\n"
                   f"📊 Всего: {len(submissions)}",
        color=config.RASPBERRY_COLOR
    )
    
    if submissions:
        view = PlayerProfileView(submissions, player)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    else:
        await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="admin_disqualify", description="Дисквалификация/восстановление игрока (только для админов)")
async def admin_disqualify(interaction: discord.Interaction, user: discord.Member, action: str):
    """Команда для дисквалификации/снятия дисквалификации игрока."""
    if not await has_admin_permissions(interaction):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    if action not in ["disqualify", "cancel"]:
        await interaction.response.send_message("❌ Неверное действие. Используйте 'disqualify' или 'cancel'.", ephemeral=True)
        return
    
    player = database.get_player(user.id)
    if not player:
        await interaction.response.send_message("❌ Пользователь не зарегистрирован на ивент.", ephemeral=True)
        return
    
    if action == "disqualify":
        success = database.disqualify_player(user.id)
        action_text = "дисквалифицирован"
        notification_title = "❌ Вы дисквалифицированы"
        notification_desc = "Вы были дисквалифицированы с ивента. Ваши скриншоты больше не засчитываются."
    else:
        success = database.cancel_disqualification(user.id)
        action_text = "восстановлен"
        notification_title = "✅ Дисквалификация снята"
        notification_desc = "Ваша дисквалификация была снята. Вы можете продолжить участие в ивенте."
    
    if success:
        # Уведомляем игрока
        try:
            embed_notification = discord.Embed(
                title=notification_title,
                description=notification_desc,
                color=config.RASPBERRY_COLOR
            )
            await user.send(embed=embed_notification)
            print(f"✅ Уведомление о {action_text} отправлено пользователю {user}")
        except discord.Forbidden:
            print(f"❌ Не удалось отправить DM пользователю {user.id} - закрыты личные сообщения")
        except discord.HTTPException as e:
            print(f"❌ Ошибка HTTP при отправке DM: {e}")
        except Exception as e:
            print(f"❌ Неожиданная ошибка при отправке DM: {e}")
        
        await interaction.response.send_message(f"✅ Игрок {user.mention} {action_text}.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Ошибка при выполнении операции.", ephemeral=True)

@bot.tree.command(name="calculate_payments", description="Расчет выплат игрокам (только для админов)")
async def calculate_payments(interaction: discord.Interaction):
    """Команда для расчета выплат."""
    if not await has_admin_permissions(interaction):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    approved_stats = database.get_approved_screenshots_stats()
    
    if not approved_stats:
        embed = discord.Embed(
            title="💰 Расчет выплат",
            description="❌ Нет игроков с одобренными скриншотами для выплат.",
            color=config.RASPBERRY_COLOR
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    # Подсчитываем общую статистику
    total_players = len([p for p in approved_stats if p[3] > 0])
    total_screenshots = sum(p[3] for p in approved_stats)
    total_amount = total_screenshots * 10000
    
    # Создаем основной embed с информацией
    main_embed = discord.Embed(
        title="💰 Расчет выплат участникам ивента",
        description=f"**Общая статистика:**\n"
                   f"👥 Игроков к выплате: {total_players}\n"
                   f"📸 Одобренных скриншотов: {total_screenshots}\n"
                   f"💵 Общая сумма: {total_amount:,} монет\n\n"
                   f"**Формат команды:** `/givemoney StaticID сумма EventMagic`\n"
                   f"**Награда:** 10,000 монет за каждый одобренный скриншот",
        color=config.RASPBERRY_COLOR
    )
    main_embed.set_footer(text="Скопируйте команды из сообщений ниже")
    
    await interaction.followup.send(embed=main_embed, ephemeral=True)
    
    # Создаем команды выплат
    payment_commands = []
    for discord_id, nickname, static_id, approved_count in approved_stats:
        if approved_count > 0:
            amount = approved_count * 10000
            payment_commands.append(f"/givemoney {static_id} {amount} EventMagic")
    
    # Разбиваем команды на группы для удобного копирования
    commands_per_message = 10
    for i in range(0, len(payment_commands), commands_per_message):
        chunk_commands = payment_commands[i:i + commands_per_message]
        
        # Создаем embed для группы команд
        chunk_embed = discord.Embed(
            title=f"📋 Команды выплат (группа {i//commands_per_message + 1})",
            description="```\n" + "\n".join(chunk_commands) + "\n```",
            color=config.RASPBERRY_COLOR
        )
        
        # Добавляем информацию о игроках в этой группе
        players_info = []
        for cmd in chunk_commands:
            static_id = cmd.split()[1]
            # Находим игрока по static_id
            for discord_id, nickname, player_static_id, approved_count in approved_stats:
                if player_static_id == static_id:
                    amount = approved_count * 10000
                    players_info.append(f"• {nickname} ({static_id}): {approved_count} скриншотов = {amount:,} монет")
                    break
        
        chunk_embed.add_field(
            name="Детали выплат:",
            value="\n".join(players_info),
            inline=False
        )
        
        chunk_embed.set_footer(text="Выделите текст в блоке выше для быстрого копирования")
        
        await interaction.followup.send(embed=chunk_embed, ephemeral=True)

@bot.tree.command(name="reset_stats", description="Сброс всех статистик (только для админов)")
async def reset_statistics(interaction: discord.Interaction):
    """Команда для сброса всех статистик."""
    if not await has_admin_permissions(interaction):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    view = ResetConfirmationView()
    await interaction.response.send_message(
        "⚠️ **ВНИМАНИЕ!** Вы собираетесь удалить все статистики и профили игроков.\n"
        "Это действие необратимо. Вы уверены?",
        view=view,
        ephemeral=True
    )

class ResetConfirmationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label='✅ Да, сбросить', style=discord.ButtonStyle.danger)
    async def confirm_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = database.reset_all_statistics()
        
        if success:
            await interaction.response.send_message("✅ Все статистики успешно сброшены.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Ошибка при сбросе статистик.", ephemeral=True)

    @discord.ui.button(label='❌ Отмена', style=discord.ButtonStyle.secondary)
    async def cancel_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Сброс отменен.", ephemeral=True)

# Запуск бота
if __name__ == "__main__":
    token = config.BOT_TOKEN
    if not token:
        print("❌ Ошибка: BOT_TOKEN не найден в переменных окружения")
        exit(1)
    
    bot.run(token)