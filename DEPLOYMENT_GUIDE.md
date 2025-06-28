# Discord Bot Deployment Guide

## Общая информация

Данный Discord бот написан на Python и использует:
- **py-cord** (современная версия discord.py)
- **SQLite** для базы данных (локальный файл)
- **python-dotenv** для переменных окружения
- **pytz** для работы с часовыми поясами

## Требования для развертывания

### Системные требования
- **Python 3.11** или новее
- **pip** (менеджер пакетов Python)
- Постоянное интернет-соединение
- Минимум 512MB RAM
- 1GB свободного места на диске

### Файлы для копирования
Скопируйте эти файлы на новый сервер:
```
main_fixed.py       # Основной файл бота
database.py         # Работа с базой данных
config.py          # Настройки конфигурации
pyproject.toml     # Зависимости проекта
.env               # Переменные окружения (создать заново)
```

## Пошаговая инструкция развертывания

### Шаг 1: Настройка сервера

**Для Ubuntu/Debian серверов:**
```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Python 3.11 и pip
sudo apt install python3.11 python3.11-pip python3.11-venv -y

# Создаем рабочую директорию
mkdir discord-bot
cd discord-bot
```

**Для CentOS/RHEL серверов:**
```bash
# Обновляем систему
sudo yum update -y

# Устанавливаем Python 3.11
sudo yum install python3.11 python3.11-pip -y

# Создаем рабочую директорию
mkdir discord-bot
cd discord-bot
```

### Шаг 2: Установка зависимостей

```bash
# Создаем виртуальное окружение
python3.11 -m venv bot_env

# Активируем окружение
source bot_env/bin/activate

# Устанавливаем зависимости
pip install py-cord python-dotenv pytz

# Проверяем установку
pip list
```

### Шаг 3: Настройка файлов

**Создайте файл .env:**
```bash
nano .env
```

**Содержимое .env файла:**
```
BOT_TOKEN=ВАШ_ТОКЕН_БОТА_DISCORD
```

**Настройте config.py:**
```python
# Обновите эти значения для вашего сервера
GUILD_ID = ВАШ_ID_СЕРВЕРА_DISCORD
ADMIN_ROLE_ID = ID_РОЛИ_АДМИНИСТРАТОРА

# Временные зоны и даты ивента
EVENT_START = "2025-06-28T00:00:00"
EVENT_END = "2025-07-05T23:59:59"
TIMEZONE = "Europe/Moscow"  # Измените на ваш часовой пояс
```

### Шаг 4: Копирование файлов

Скопируйте все файлы проекта в директорию `discord-bot/`:
```bash
# Способ 1: через scp (с другого сервера)
scp user@old-server:/path/to/bot/* ./

# Способ 2: через git clone (если код в репозитории)
git clone YOUR_REPOSITORY_URL .

# Способ 3: загрузка через FileZilla/WinSCP
```

### Шаг 5: Тестовый запуск

```bash
# Активируем окружение если не активировано
source bot_env/bin/activate

# Запускаем бота
python main_fixed.py
```

Должно появиться сообщение: `Фотограф#XXXX подключен к Discord!`

### Шаг 6: Настройка автозапуска

**Создайте systemd сервис (для Ubuntu/CentOS):**
```bash
sudo nano /etc/systemd/system/discord-bot.service
```

**Содержимое сервиса:**
```ini
[Unit]
Description=Discord Event Bot
After=network.target

[Service]
Type=simple
User=ВАШ_ПОЛЬЗОВАТЕЛЬ
WorkingDirectory=/home/ВАШ_ПОЛЬЗОВАТЕЛЬ/discord-bot
Environment=PATH=/home/ВАШ_ПОЛЬЗОВАТЕЛЬ/discord-bot/bot_env/bin
ExecStart=/home/ВАШ_ПОЛЬЗОВАТЕЛЬ/discord-bot/bot_env/bin/python main_fixed.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**Запуск сервиса:**
```bash
# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable discord-bot

# Запускаем сервис
sudo systemctl start discord-bot

# Проверяем статус
sudo systemctl status discord-bot

# Просмотр логов
sudo journalctl -u discord-bot -f
```

## Специфичные инструкции для SparkedHost

### Панель управления SparkedHost
1. **Выберите VPS с Ubuntu 22.04**
2. **Минимальная конфигурация:** 1GB RAM, 10GB SSD
3. **После создания VPS подключитесь по SSH**

### SSH подключение
```bash
ssh root@ВАШ_IP_АДРЕС
```

### Установка для SparkedHost
```bash
# Обновляем систему
apt update && apt upgrade -y

# Устанавливаем необходимые пакеты
apt install python3.11 python3.11-pip python3.11-venv nano git htop -y

# Создаем пользователя для бота
useradd -m -s /bin/bash botuser
su - botuser

# Далее следуйте основной инструкции начиная с Шага 2
```

## Важные настройки Discord

### В Discord Developer Portal:
1. **Bot Token:** Скопируйте токен в .env файл
2. **Privileged Gateway Intents:** Включите "Message Content Intent"
3. **Bot Permissions:** Минимум 2048 (Use Slash Commands)

### Получение ID сервера и роли:
```
1. Включите Developer Mode в Discord
2. Правый клик на сервер → "Copy Server ID" 
3. Правый клик на роль администратора → "Copy Role ID"
4. Обновите config.py с полученными ID
```

## Управление ботом на сервере

### Полезные команды
```bash
# Статус бота
sudo systemctl status discord-bot

# Остановка бота
sudo systemctl stop discord-bot

# Запуск бота
sudo systemctl start discord-bot

# Перезапуск бота
sudo systemctl restart discord-bot

# Просмотр логов в реальном времени
sudo journalctl -u discord-bot -f

# Обновление кода (если есть изменения)
cd discord-bot
git pull  # или скопируйте новые файлы
sudo systemctl restart discord-bot
```

### Резервное копирование
```bash
# Создание бэкапа базы данных
cp event_data.db backup/event_data_$(date +%Y%m%d).db

# Автоматический бэкап (crontab)
crontab -e
# Добавьте строку для ежедневного бэкапа в 3:00
0 3 * * * cp /home/botuser/discord-bot/event_data.db /home/botuser/backup/event_data_$(date +\%Y\%m\%d).db
```

## Решение проблем

### Бот не подключается
1. Проверьте правильность BOT_TOKEN в .env
2. Убедитесь что бот добавлен на сервер с правильными правами
3. Проверьте интернет-соединение сервера

### Команды не работают
1. Убедитесь что GUILD_ID корректный в config.py
2. Проверьте что "Message Content Intent" включен
3. Перезапустите бота после изменений

### База данных ошибки
1. Проверьте права доступа к файлу event_data.db
2. Убедитесь что есть свободное место на диске
3. Файл базы должен быть в той же папке что и main_fixed.py

## Мониторинг и логи

### Просмотр статуса системы
```bash
# Использование ресурсов
htop

# Место на диске
df -h

# Логи системы
journalctl -xe

# Сетевые соединения
netstat -tuln
```

### Настройка уведомлений
Рекомендуется настроить мониторинг через:
- **Uptimerobot** (бесплатный HTTP/Ping мониторинг)
- **Telegram уведомления** при падении сервиса
- **Email алерты** через systemd

## Заключение

После выполнения всех шагов ваш Discord бот будет:
- ✅ Автоматически запускаться при перезагрузке сервера
- ✅ Перезапускаться при ошибках
- ✅ Логировать все действия
- ✅ Иметь резервные копии базы данных

Бот полностью готов к продакшн использованию на любом VPS провайдере.