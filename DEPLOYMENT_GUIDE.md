# Руководство по развертыванию Discord бота

## Системные требования

- Python 3.8 или выше
- Стабильное интернет-соединение
- VPS или выделенный сервер (рекомендуется Ubuntu 20.04+)

## Файлы для загрузки на сервер

Скопируйте следующие файлы на ваш сервер:

### Основные файлы
- `main_discord_py.py` - **ГЛАВНЫЙ ФАЙЛ БОТА** (запускать этот)
- `database.py` - модуль работы с базой данных
- `config.py` - настройки бота
- `.env` - файл с токеном бота

### Дополнительные файлы
- `pyproject.toml` - зависимости Python
- `uv.lock` - точные версии пакетов

## Пошаговая установка

### 1. Подготовка сервера (Ubuntu/Debian)

```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Python и pip
sudo apt install python3 python3-pip python3-venv git -y

# Создаем пользователя для бота (опционально)
sudo useradd -m -s /bin/bash discordbot
sudo su - discordbot
```

### 2. Настройка проекта

```bash
# Создаем директорию проекта
mkdir discord-event-bot
cd discord-event-bot

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install discord.py==2.5.2 python-dotenv pytz
```

### 3. Копирование файлов

Загрузите файлы проекта на сервер любым способом:
- SCP/SFTP
- Git clone (если проект в репозитории)
- Прямое копирование

### 4. Настройка конфигурации

Отредактируйте файл `config.py`:

```python
# Установите ID вашего Discord сервера
GUILD_ID = 123456789012345678  # Замените на ID вашего сервера

# Установите ID роли администратора (опционально)
ADMIN_ROLE_ID = 987654321098765432  # Замените на ID роли админа

# Настройте временную зону
TIMEZONE = pytz.timezone('Europe/Moscow')  # Измените по необходимости

# Даты ивента (ISO формат)
EVENT_START = "2025-01-01T00:00:00"  # Начало ивента
EVENT_END = "2025-01-31T23:59:59"    # Конец ивента
```

Создайте файл `.env` с токеном бота:

```env
BOT_TOKEN=ваш_токен_бота_здесь
```

### 5. Запуск бота

```bash
# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем основной файл бота
python main_discord_py.py
```

## Настройка автозапуска (systemd)

Создайте systemd сервис для автоматического запуска:

```bash
sudo nano /etc/systemd/system/discord-bot.service
```

Содержимое файла:

```ini
[Unit]
Description=Discord Event Bot
After=network.target

[Service]
Type=simple
User=discordbot
WorkingDirectory=/home/discordbot/discord-event-bot
Environment=PATH=/home/discordbot/discord-event-bot/venv/bin
ExecStart=/home/discordbot/discord-event-bot/venv/bin/python main_discord_py.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активируйте сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl enable discord-bot.service
sudo systemctl start discord-bot.service

# Проверьте статус
sudo systemctl status discord-bot.service

# Просмотр логов
sudo journalctl -u discord-bot.service -f
```

## Управление ботом

### Запуск
```bash
sudo systemctl start discord-bot.service
```

### Остановка
```bash
sudo systemctl stop discord-bot.service
```

### Перезапуск
```bash
sudo systemctl restart discord-bot.service
```

### Просмотр логов
```bash
sudo journalctl -u discord-bot.service -f
```

## Настройки Discord

### 1. В Discord Developer Portal:

- Включите "Message Content Intent"
- Включите "Server Members Intent" (если нужно)
- Убедитесь что бот имеет права:
  - Send Messages
  - Use Slash Commands
  - Read Message History
  - Embed Links

### 2. На вашем Discord сервере:

- Пригласите бота с нужными правами
- Убедитесь что у бота есть роль с административными правами
- Проверьте что бот может видеть каналы где будут использоваться команды

## Резервное копирование

База данных SQLite сохраняется в файле `event_data.db`. Регулярно делайте его резервные копии:

```bash
# Создание бэкапа
cp event_data.db backup_$(date +%Y%m%d_%H%M%S).db

# Автоматический бэкап (добавить в crontab)
0 2 * * * cp /home/discordbot/discord-event-bot/event_data.db /home/discordbot/backups/backup_$(date +\%Y\%m\%d).db
```

## Мониторинг

Для мониторинга состояния бота используйте:

```bash
# Проверка процесса
ps aux | grep python | grep main_discord_py

# Мониторинг логов в реальном времени
sudo journalctl -u discord-bot.service -f

# Проверка использования ресурсов
htop
```

## Устранение неполадок

### Бот не запускается:
1. Проверьте токен в файле `.env`
2. Убедитесь что все зависимости установлены
3. Проверьте логи: `journalctl -u discord-bot.service`

### Команды не работают:
1. Убедитесь что GUILD_ID правильный
2. Проверьте права бота на сервере
3. Перезапустите бота для синхронизации команд

### Личные сообщения не работают:
1. Проверьте настройки конфиденциальности пользователей
2. Убедитесь что включен "Message Content Intent"
3. Проверьте права бота на отправку DM

## Обновление бота

```bash
# Остановите бота
sudo systemctl stop discord-bot.service

# Обновите файлы проекта
# (скопируйте новые версии файлов)

# Обновите зависимости (если нужно)
source venv/bin/activate
pip install --upgrade discord.py python-dotenv pytz

# Запустите бота
sudo systemctl start discord-bot.service
```

## Главный файл для запуска

**ВАЖНО:** Главный файл для запуска бота - `main_discord_py.py`

Этот файл содержит всю логику бота, включая:
- Обработку команд
- Систему регистрации
- Модерацию скриншотов
- Административные функции
- Систему уведомлений

Не запускайте другие файлы (main.py, main_simple.py и т.д.) - они предназначены для разработки и тестирования.