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
        
        self.static_id = discord.ui.InputText(
            label='Ваш StaticID',
            placeholder='Введите ваш StaticID',
            required=True,
            max_length=50
        )
        
        self.nickname = discord.ui.InputText(
            label='Ваш игровой Nickname',
            placeholder='Введите ваш игровой никнейм',
            required=True,
            max_length=50
        )
        
        self.add_item(self.static_id)
        self.add_item(self.nickname)

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
                
                # Отправляем приветственное сообщение в ЛС
                try:
                    dm_embed = discord.Embed(
                        title="🎉 Добро пожаловать в ивент поиска локаций!",
                        description=f"Привет, **{nickname_value}**!\n\nВы успешно зарегистрированы с StaticID: `{static_id_value}`\n\n**Как участвовать:**\n• Отправляйте скриншоты локаций в этот чат\n• Каждый одобренный скриншот = $10,000\n• Ивент проходит: {format_event_dates()}\n\nУдачи в поисках! 🔍",
                        color=config.RASPBERRY_COLOR
                    )
                    await interaction.user.send(embed=dm_embed)
                except:
                    pass  # Игнорируем ошибку если не удалось отправить ЛС
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

# Классы для просмотра скриншотов и модерации
class ScreenshotSelect(discord.ui.Select):
    def __init__(self, submissions, player_info):
        self.submissions = submissions
        self.player_info = player_info
        
        options = []
        for i, sub in enumerate(submissions[:25]):  # Discord limit 25
            timestamp = datetime.datetime.fromisoformat(sub['submission_time'])
            date_str = timestamp.strftime("%d.%m %H:%M")
            
            # Проверяем статус одобрения
            if sub.get('is_approved') == 1 or sub.get('is_approved') is True:
                status_emoji = "✅"
                status_text = "Одобрен"
            elif sub.get('is_approved') == 0 or sub.get('is_approved') is False:
                status_emoji = "❌"
                status_text = "Отклонен"
            else:
                status_emoji = "⏳"
                status_text = "На модерации"
            
            label = f"Скриншот #{i+1} ({date_str})"
            description = f"{status_emoji} {status_text}"
            
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
        try:
            if self.disabled:
                return
                
            submission_id = int(self.values[0])
            submission = database.get_submission_by_id(submission_id)
            
            if not submission:
                await interaction.response.send_message("❌ Скриншот не найден.", ephemeral=True)
                return
            
            timestamp = datetime.datetime.fromisoformat(submission['submission_time'])
            date_str = timestamp.strftime("%d.%m.%Y в %H:%M")
            
            # Проверяем статус одобрения
            if submission.get('is_approved') == 1 or submission.get('is_approved') is True:
                status_text = "✅ Одобрен"
            elif submission.get('is_approved') == 0 or submission.get('is_approved') is False:
                status_text = "❌ Отклонен"
            else:
                status_text = "⏳ На модерации"
            
            embed = discord.Embed(
                title=f"📸 Скриншот #{submission_id}",
                description=f"**Игрок:** {self.player_info['nickname']}\n**Дата:** {date_str}\n**Статус:** {status_text}",
                color=config.RASPBERRY_COLOR
            )
            embed.set_image(url=submission['screenshot_url'])
            
            # Добавляем кнопки модерации только для админов
            view = None
            if interaction.user.guild_permissions.administrator:
                view = ScreenshotModerationView(submission_id, submission.get('is_approved', False))
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            print(f"Ошибка просмотра скриншота: {e}")
            await interaction.response.send_message("❌ Произошла ошибка.", ephemeral=True)

class RejectReasonModal(discord.ui.Modal):
    def __init__(self, submission_id, view):
        super().__init__(title="Причина отклонения скриншота")
        self.submission_id = submission_id
        self.view = view
        
        self.reason = discord.ui.InputText(
            label="Причина отклонения",
            placeholder="Опишите причину отклонения скриншота...",
            style=discord.InputTextStyle.paragraph,
            required=True,
            max_length=500
        )
        self.add_item(self.reason)

    async def callback(self, interaction: discord.Interaction):
        try:
            # Получаем данные скриншота и игрока
            submission = database.get_submission_by_id(self.submission_id)
            if not submission:
                await interaction.response.send_message("❌ Скриншот не найден.", ephemeral=True)
                return
            
            player = database.get_player(submission['discord_id'])
            if not player:
                await interaction.response.send_message("❌ Игрок не найден.", ephemeral=True)
                return
            
            # Отклоняем скриншот
            success = database.reject_screenshot(self.submission_id)
            if success:
                # Отправляем уведомление игроку
                notification_sent = False
                try:
                    user = bot.get_user(submission['discord_id'])
                    if user is None:
                        # Пытаемся получить пользователя через fetch
                        user = await bot.fetch_user(submission['discord_id'])
                    
                    if user:
                        # Получаем личный номер скриншота игрока
                        personal_number = database.get_player_screenshot_number(submission['discord_id'], self.submission_id)
                        embed = discord.Embed(
                            title="❌ Скриншот отклонен",
                            description=f"**Ваш {personal_number}-й скриншот** был отклонен администратором.\n\n**Причина:** {self.reason.value}\n\nВы можете отправить новый скриншот.",
                            color=0xFF0000
                        )
                        embed.set_image(url=submission['screenshot_url'])
                        await user.send(embed=embed)
                        notification_sent = True
                        print(f"Уведомление об отклонении отправлено пользователю {user.name}")
                    else:
                        print(f"Не удалось найти пользователя с ID {submission['discord_id']}")
                except Exception as e:
                    print(f"Ошибка отправки уведомления об отклонении: {e}")
                    print(f"Тип ошибки: {type(e).__name__}")
                    print(f"Детали: {str(e)}")
                
                # Отправляем ответ с информацией о результате
                status_message = f"❌ Скриншот отклонен!\nПричина: {self.reason.value}"
                if notification_sent:
                    status_message += "\nИгроку отправлено уведомление."
                else:
                    status_message += "\n⚠️ Не удалось отправить уведомление игроку."
                
                await interaction.response.send_message(status_message, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Ошибка при отклонении.", ephemeral=True)
        except Exception as e:
            print(f"Ошибка отклонения: {e}")
            await interaction.response.send_message("❌ Произошла ошибка.", ephemeral=True)

class ScreenshotModerationView(discord.ui.View):
    def __init__(self, submission_id, current_status):
        super().__init__(timeout=300)
        self.submission_id = submission_id
        self.current_status = current_status
    
    async def update_parent_stats_if_needed(self, interaction):
        """Обновляет статистику в родительском сообщении admin_stats если возможно"""
        try:
            # Этот метод может быть расширен в будущем для обновления статистики
            pass
        except Exception as e:
            print(f"Ошибка обновления статистики: {e}")

    @discord.ui.button(label="✅ Одобрить", style=discord.ButtonStyle.success)
    async def approve_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            # Получаем данные скриншота и игрока
            submission = database.get_submission_by_id(self.submission_id)
            if not submission:
                await interaction.response.send_message("❌ Скриншот не найден.", ephemeral=True)
                return
            
            player = database.get_player(submission['discord_id'])
            if not player:
                await interaction.response.send_message("❌ Игрок не найден.", ephemeral=True)
                return
            
            success = database.approve_screenshot(self.submission_id)
            if success:
                # Отправляем уведомление игроку
                notification_sent = False
                try:
                    user = bot.get_user(submission['discord_id'])
                    if user is None:
                        # Пытаемся получить пользователя через fetch
                        user = await bot.fetch_user(submission['discord_id'])
                    
                    if user:
                        # Получаем личный номер скриншота игрока
                        personal_number = database.get_player_screenshot_number(submission['discord_id'], self.submission_id)
                        embed = discord.Embed(
                            title="✅ Скриншот одобрен!",
                            description=f"**Ваш {personal_number}-й скриншот** был одобрен администратором!\n\nПродолжайте искать локации!",
                            color=config.RASPBERRY_COLOR
                        )
                        embed.set_image(url=submission['screenshot_url'])
                        await user.send(embed=embed)
                        notification_sent = True
                        print(f"Уведомление об одобрении отправлено пользователю {user.name}")
                    else:
                        print(f"Не удалось найти пользователя с ID {submission['discord_id']}")
                except Exception as e:
                    print(f"Ошибка отправки уведомления об одобрении: {e}")
                    print(f"Тип ошибки: {type(e).__name__}")
                    print(f"Детали: {str(e)}")
                
                # Обновляем кнопки после одобрения
                button.disabled = True
                button.style = discord.ButtonStyle.secondary
                button.label = "✅ Одобрено"
                
                # Отключаем кнопку отклонения
                for item in self.children:
                    if item.label and "Отклонить" in item.label:
                        item.disabled = True
                        item.style = discord.ButtonStyle.secondary
                
                # Обновляем статус сообщения в зависимости от успеха уведомления
                status_message = "✅ Скриншот одобрен!"
                if notification_sent:
                    status_message += "\nИгроку отправлено уведомление."
                else:
                    status_message += "\n⚠️ Не удалось отправить уведомление игроку."
                
                await interaction.response.edit_message(view=self)
                await interaction.followup.send(status_message, ephemeral=True)
                
                # Обновляем статистику в родительском сообщении admin_stats если оно есть
                await self.update_parent_stats_if_needed(interaction)
            else:
                await interaction.response.send_message("❌ Ошибка при одобрении.", ephemeral=True)
        except Exception as e:
            print(f"Ошибка одобрения: {e}")
            await interaction.response.send_message("❌ Произошла ошибка.", ephemeral=True)

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger)
    async def reject_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            modal = RejectReasonModal(self.submission_id, self)
            await interaction.response.send_modal(modal)
        except Exception as e:
            print(f"Ошибка отклонения: {e}")
            await interaction.response.send_message("❌ Произошла ошибка.", ephemeral=True)

class PlayerSelect(discord.ui.Select):
    def __init__(self, players_data, page=0):
        self.page = page
        self.players_per_page = 25
        self.total_players = len(players_data)
        self.total_pages = max(1, (self.total_players - 1) // self.players_per_page + 1)
        
        # Получаем игроков для текущей страницы
        start_idx = page * self.players_per_page
        end_idx = start_idx + self.players_per_page
        current_page_players = players_data[start_idx:end_idx]
        
        options = []
        for player in current_page_players:
            discord_id, nickname, screenshot_count = player
            display_name = get_user_tag(discord_id)
            
            # Получаем детальную статистику модерации для каждого игрока
            submissions = database.get_player_submissions(discord_id)
            approved_count = len([s for s in submissions if s['is_approved'] == 1 or s['is_approved'] is True])
            rejected_count = len([s for s in submissions if s['is_approved'] == 0 or s['is_approved'] is False])
            pending_count = len([s for s in submissions if s['is_approved'] is None])
            
            label = f"{nickname} ({display_name})"
            
            # Формируем описание с статистикой модерации
            if screenshot_count == 0:
                description = "Нет скриншотов"
            else:
                description = f"✅{approved_count} ❌{rejected_count} ⏳{pending_count}"
                if pending_count > 0:
                    description += " • ТРЕБУЕТ МОДЕРАЦИИ"
            
            options.append(discord.SelectOption(
                label=label[:100],
                description=description[:100],
                value=str(discord_id)
            ))
        
        placeholder = f"Выберите игрока (стр. {page + 1}/{self.total_pages})..." if options else "Нет зарегистрированных игроков"
        
        super().__init__(
            placeholder=placeholder,
            options=options if options else [discord.SelectOption(label="Пусто", value="0")],
            disabled=not options
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            if self.disabled:
                return
                
            selected_discord_id = int(self.values[0])
            player = database.get_player(selected_discord_id)
            if not player:
                await interaction.response.send_message("❌ Игрок не найден.", ephemeral=True)
                return
            
            submissions = database.get_player_submissions(selected_discord_id)
            approved_count = len([s for s in submissions if s.get('is_approved') == 1 or s.get('is_approved') is True])
            rejected_count = len([s for s in submissions if s.get('is_approved') == 0 or s.get('is_approved') is False])
            pending_count = len([s for s in submissions if s.get('is_approved') is None])
            
            embed = discord.Embed(
                title=f"👤 Профиль игрока",
                color=config.RASPBERRY_COLOR
            )
            embed.add_field(name="Никнейм", value=player['nickname'], inline=True)
            embed.add_field(name="Discord", value=get_user_tag(selected_discord_id), inline=True)
            embed.add_field(name="StaticID", value=player['static_id'], inline=True)
            embed.add_field(name="✅ Одобрено", value=str(approved_count), inline=True)
            embed.add_field(name="❌ Отклонено", value=str(rejected_count), inline=True)
            embed.add_field(name="⏳ На модерации", value=str(pending_count), inline=True)
            embed.add_field(name="Статус", value="❌ Дисквалифицирован" if player['is_disqualified'] else "✅ Активен", inline=True)
            
            # Добавляем выбор скриншотов если они есть
            view = None
            if submissions:
                view = PlayerProfileView(submissions, player)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            print(f"Ошибка выбора игрока: {e}")
            await interaction.response.send_message("❌ Произошла ошибка.", ephemeral=True)

class PlayerProfileView(discord.ui.View):
    def __init__(self, submissions, player_info):
        super().__init__(timeout=300)
        self.add_item(ScreenshotSelect(submissions, player_info))

class PlayerListView(discord.ui.View):
    def __init__(self, players_data):
        super().__init__(timeout=300)
        self.players_data = players_data
        self.current_page = 0
        self.total_pages = max(1, (len(players_data) - 1) // 25 + 1)
        
        # Добавляем выпадающий список для текущей страницы
        self.player_select = PlayerSelect(players_data, self.current_page)
        self.add_item(self.player_select)
        
        # Добавляем кнопки навигации только если больше одной страницы
        if self.total_pages > 1:
            self.update_navigation_buttons()
    
    def update_navigation_buttons(self):
        """Обновляет состояние кнопок навигации"""
        # Удаляем старые кнопки навигации если они есть
        items_to_remove = []
        for item in self.children:
            if hasattr(item, 'custom_id') and item.custom_id in ['prev_page', 'next_page']:
                items_to_remove.append(item)
        
        for item in items_to_remove:
            self.remove_item(item)
        
        # Добавляем новые кнопки
        prev_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="◀ Предыдущая",
            disabled=self.current_page <= 0,
            custom_id='prev_page'
        )
        prev_button.callback = self.prev_page
        
        next_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Следующая ▶",
            disabled=self.current_page >= self.total_pages - 1,
            custom_id='next_page'
        )
        next_button.callback = self.next_page
        
        self.add_item(prev_button)
        self.add_item(next_button)
    
    async def prev_page(self, interaction: discord.Interaction):
        """Переход на предыдущую страницу"""
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_page(interaction)
    
    async def next_page(self, interaction: discord.Interaction):
        """Переход на следующую страницу"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await self.update_page(interaction)
    
    async def update_page(self, interaction: discord.Interaction):
        """Обновляет страницу с новым списком игроков"""
        # Удаляем старый select
        self.remove_item(self.player_select)
        
        # Создаем новый select для текущей страницы
        self.player_select = PlayerSelect(self.players_data, self.current_page)
        self.add_item(self.player_select)
        
        # Обновляем кнопки навигации
        self.update_navigation_buttons()
        
        # Получаем оригинальное embed сообщение для обновления
        original_embed = interaction.message.embeds[0] if interaction.message.embeds else None
        
        await interaction.response.edit_message(embed=original_embed, view=self)

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
        
        success = database.add_submission(message.author.id, attachment.url)
        
        if success:
            submissions = database.get_player_submissions(message.author.id)
            count = len(submissions)
            
            embed = discord.Embed(
                title="✅ Ваш скриншот принят в обработку",
                description=f"Скриншот успешно получен и добавлен в систему.\n\n**Всего отправлено:** {count} скриншотов\n**Статус:** ⏳ На модерации администраторами\n\nВы получите уведомление когда скриншот будет проверен.",
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
        leaderboard_by_approved = database.get_leaderboard_by_approved()
        approved_stats = database.get_approved_screenshots_stats()
        
        # Считаем общую статистику
        total_submissions = sum(player[2] for player in leaderboard_by_approved)
        total_approved = sum(player[3] for player in leaderboard_by_approved)
        
        embed = discord.Embed(
            title="📊 Статистика ивента",
            color=config.RASPBERRY_COLOR
        )
        embed.add_field(name="👥 Всего игроков", value=str(total_players), inline=True)
        embed.add_field(name="📸 Всего скриншотов", value=str(total_submissions), inline=True)
        embed.add_field(name="✅ Одобренных скриншотов", value=str(total_approved), inline=True)
        embed.add_field(name="📅 Период ивента", value=format_event_dates(), inline=False)
        embed.add_field(name="⏰ Статус", value="🟢 Активен" if is_event_active() else "🔴 Неактивен", inline=True)
        
        # Показываем топ-5 игроков по одобренным скриншотам
        if leaderboard_by_approved:
            top_players = leaderboard_by_approved[:5]
            top_text = ""
            for i, (discord_id, nickname, total_screenshots, approved_count) in enumerate(top_players, 1):
                user_tag = get_user_tag(discord_id)
                top_text += f"{i}. {nickname} ({user_tag}) - {approved_count} одобренных ({total_screenshots} всего)\n"
            embed.add_field(name="🏆 Топ-5 игроков (по одобренным)", value=top_text or "Нет данных", inline=False)
        
        # Преобразуем данные для выпадающего списка (discord_id, nickname, total_count)
        player_list_data = [(player[0], player[1], player[2]) for player in leaderboard_by_approved]
        view = PlayerListView(player_list_data) if player_list_data else None
        await ctx.respond(embed=embed, view=view, ephemeral=True)
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
        approved_count = len([s for s in submissions if s.get('is_approved') == 1 or s.get('is_approved') is True])
        rejected_count = len([s for s in submissions if s.get('is_approved') == 0 or s.get('is_approved') is False])
        pending_count = len([s for s in submissions if s.get('is_approved') is None])
        
        embed = discord.Embed(
            title=f"👤 Профиль игрока",
            color=config.RASPBERRY_COLOR
        )
        embed.add_field(name="Никнейм", value=player['nickname'], inline=True)
        embed.add_field(name="Discord", value=f"@{user.name}", inline=True)
        embed.add_field(name="StaticID", value=player['static_id'], inline=True)
        embed.add_field(name="✅ Одобрено", value=str(approved_count), inline=True)
        embed.add_field(name="❌ Отклонено", value=str(rejected_count), inline=True)
        embed.add_field(name="⏳ На модерации", value=str(pending_count), inline=True)
        embed.add_field(name="Статус", value="❌ Дисквалифицирован" if player['is_disqualified'] else "✅ Активен", inline=True)
        
        view = PlayerProfileView(submissions, player) if submissions else None
        await ctx.respond(embed=embed, view=view, ephemeral=True)
    except Exception as e:
        print(f"Ошибка команды /admin_profile: {e}")
        await ctx.respond("❌ Произошла ошибка.", ephemeral=True)

@bot.slash_command(name='admin_disqualify', description='Управление дисквалификацией игрока (только для администраторов)', guild_ids=[config.GUILD_ID])
async def admin_disqualify(ctx, user: discord.Member, action: discord.Option(str, "Действие", choices=["disqualify", "cancel"])):
    """Команда для дисквалификации/снятия дисквалификации игрока."""
    try:
        if not await has_admin_permissions(ctx):
            return
        
        player = database.get_player(user.id)
        if not player:
            await ctx.respond(f"❌ Пользователь {user.mention} не зарегистрирован.", ephemeral=True)
            return
        
        if action == "disqualify":
            if player['is_disqualified']:
                await ctx.respond(f"❌ Игрок {user.mention} уже дисквалифицирован.", ephemeral=True)
                return
                
            if database.disqualify_player(user.id):
                # Отправляем сообщение игроку о дисквалификации
                try:
                    dm_embed = discord.Embed(
                        title="❌ Дисквалификация",
                        description=f"Вы были дисквалифицированы с ивента.\n\nВаши скриншоты больше не учитываются в конкурсе.",
                        color=0xFF0000
                    )
                    await user.send(embed=dm_embed)
                except:
                    pass  # Игнорируем ошибку если не удалось отправить ЛС
                
                embed = discord.Embed(
                    title="❌ Игрок дисквалифицирован",
                    description=f"**Игрок:** {player['nickname']} ({user.mention})\n**StaticID:** {player['static_id']}\n\nВсе скриншоты игрока помечены как недействительные.\nИгроку отправлено уведомление.",
                    color=0xFF0000
                )
                await ctx.respond(embed=embed, ephemeral=True)
            else:
                await ctx.respond("❌ Ошибка при дисквалификации.", ephemeral=True)
                
        elif action == "cancel":
            if not player['is_disqualified']:
                await ctx.respond(f"❌ Игрок {user.mention} не дисквалифицирован.", ephemeral=True)
                return
                
            if database.cancel_disqualification(user.id):
                # Отправляем сообщение игроку о восстановлении
                try:
                    dm_embed = discord.Embed(
                        title="✅ Восстановление",
                        description=f"Ваша дисквалификация с ивента была отменена.\n\nВы снова можете участвовать в конкурсе!",
                        color=config.RASPBERRY_COLOR
                    )
                    await user.send(embed=dm_embed)
                except:
                    pass  # Игнорируем ошибку если не удалось отправить ЛС
                
                embed = discord.Embed(
                    title="✅ Дисквалификация отменена",
                    description=f"**Игрок:** {player['nickname']} ({user.mention})\n**StaticID:** {player['static_id']}\n\nИгрок восстановлен в конкурсе.\nВсе его скриншоты снова действительны.\nИгроку отправлено уведомление.",
                    color=config.RASPBERRY_COLOR
                )
                await ctx.respond(embed=embed, ephemeral=True)
            else:
                await ctx.respond("❌ Ошибка при отмене дисквалификации.", ephemeral=True)
                
    except Exception as e:
        print(f"Ошибка команды /admin_disqualify: {e}")
        await ctx.respond("❌ Произошла ошибка.", ephemeral=True)

@bot.slash_command(name='calculate', description='Расчет выплат для одобренных скриншотов (только для администраторов)', guild_ids=[config.GUILD_ID])
async def calculate_payments(ctx):
    """Команда для расчета выплат."""
    try:
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
    except Exception as e:
        print(f"Ошибка команды /calculate: {e}")
        await ctx.respond("❌ Произошла ошибка.", ephemeral=True)

@bot.slash_command(name='reset_stats', description='Полный сброс статистики и профилей (только для администраторов)', guild_ids=[config.GUILD_ID])
async def reset_statistics(ctx):
    """Команда для сброса всех статистик."""
    try:
        if not await has_admin_permissions(ctx):
            return
        
        # Подтверждение действия
        embed = discord.Embed(
            title="⚠️ Подтверждение сброса",
            description="Вы действительно хотите очистить ВСЮ статистику ивента?\n\n**Это действие:**\n• Удалит всех зарегистрированных игроков\n• Удалит все скриншоты\n• Очистит всю статистику\n\n**Это действие НЕОБРАТИМО!**",
            color=0xFF0000
        )
        
        view = ResetConfirmationView()
        await ctx.respond(embed=embed, view=view, ephemeral=True)
    except Exception as e:
        print(f"Ошибка команды /reset_stats: {e}")
        await ctx.respond("❌ Произошла ошибка.", ephemeral=True)

class ResetConfirmationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="✅ Да, очистить", style=discord.ButtonStyle.danger)
    async def confirm_reset(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            success = database.reset_all_statistics()
            if success:
                embed = discord.Embed(
                    title="✅ Статистика сброшена",
                    description="Все данные ивента успешно удалены.\nБот готов к новому ивенту!",
                    color=config.RASPBERRY_COLOR
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Ошибка при сбросе статистики.", ephemeral=True)
        except Exception as e:
            print(f"Ошибка сброса статистики: {e}")
            await interaction.response.send_message("❌ Произошла ошибка.", ephemeral=True)

    @discord.ui.button(label="❌ Отмена", style=discord.ButtonStyle.secondary)
    async def cancel_reset(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Сброс статистики отменен.", ephemeral=True)

# Запуск бота
if __name__ == "__main__":
    token = config.BOT_TOKEN
    if token == "YOUR_BOT_TOKEN_HERE":
        print("Error: Please set BOT_TOKEN in environment variables")
    else:
        bot.run(token)