# database.py
import sqlite3
import datetime
from typing import Optional, List, Tuple

DATABASE_NAME = "event_data.db"

def setup_database():
    """Создает таблицы, если они еще не существуют."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Создание таблицы players
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            discord_id INTEGER PRIMARY KEY,
            static_id TEXT NOT NULL,
            nickname TEXT NOT NULL,
            registration_time TIMESTAMP NOT NULL,
            is_disqualified BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # Создание таблицы submissions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            screenshot_url TEXT NOT NULL,
            submission_time TIMESTAMP NOT NULL,
            is_valid BOOLEAN DEFAULT TRUE,
            is_approved BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (player_id) REFERENCES players (discord_id)
        )
    ''')
    
    # Добавляем поле is_approved если его нет (для обновления существующих баз)
    try:
        cursor.execute('ALTER TABLE submissions ADD COLUMN is_approved BOOLEAN DEFAULT FALSE')
    except sqlite3.OperationalError:
        pass  # Поле уже существует
    
    conn.commit()
    conn.close()

def register_player(discord_id: int, static_id: str, nickname: str) -> bool:
    """
    Добавляет нового игрока в таблицу players.
    Возвращает True при успехе, False если игрок уже существует.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли уже игрок
        cursor.execute("SELECT discord_id FROM players WHERE discord_id = ?", (discord_id,))
        if cursor.fetchone():
            conn.close()
            return False
        
        # Добавляем нового игрока
        cursor.execute('''
            INSERT INTO players (discord_id, static_id, nickname, registration_time, is_disqualified)
            VALUES (?, ?, ?, ?, FALSE)
        ''', (discord_id, static_id, nickname, datetime.datetime.utcnow()))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        conn.close()
        return False

def get_player(discord_id: int) -> Optional[dict]:
    """Получает данные игрока."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT discord_id, static_id, nickname, registration_time, is_disqualified
        FROM players WHERE discord_id = ?
    ''', (discord_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'discord_id': result[0],
            'static_id': result[1],
            'nickname': result[2],
            'registration_time': result[3],
            'is_disqualified': bool(result[4])
        }
    return None

def add_submission(player_id: int, screenshot_url: str) -> bool:
    """Добавляет новый скриншот в таблицу submissions."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO submissions (player_id, screenshot_url, submission_time, is_valid)
            VALUES (?, ?, ?, TRUE)
        ''', (player_id, screenshot_url, datetime.datetime.utcnow()))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        conn.close()
        return False

def get_player_submissions(discord_id: int) -> List[dict]:
    """Получает все скриншоты конкретного игрока."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT submission_id, screenshot_url, submission_time, is_valid, is_approved
        FROM submissions WHERE player_id = ?
        ORDER BY submission_time DESC
    ''', (discord_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    submissions = []
    for result in results:
        submissions.append({
            'submission_id': result[0],
            'screenshot_url': result[1],
            'submission_time': result[2],
            'is_valid': bool(result[3]),
            'is_approved': result[4]  # None, True, or False
        })
    
    return submissions

def get_leaderboard() -> List[Tuple[int, str, int]]:
    """
    Возвращает список игроков, отсортированный по количеству валидных скриншотов (по убыванию).
    Возвращает список кортежей: (discord_id, nickname, screenshot_count)
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.discord_id, p.nickname, COUNT(s.submission_id) as screenshot_count
        FROM players p
        LEFT JOIN submissions s ON p.discord_id = s.player_id AND s.is_valid = TRUE
        WHERE p.is_disqualified = FALSE
        GROUP BY p.discord_id, p.nickname
        ORDER BY screenshot_count DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_all_players_stats() -> int:
    """Возвращает общее количество зарегистрированных игроков."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM players")
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else 0

def disqualify_player(discord_id: int) -> bool:
    """
    Устанавливает is_disqualified в TRUE для игрока и is_valid в FALSE для всех его скриншотов.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    try:
        # Дисквалифицируем игрока
        cursor.execute('''
            UPDATE players SET is_disqualified = TRUE WHERE discord_id = ?
        ''', (discord_id,))
        
        # Делаем все его скриншоты невалидными
        cursor.execute('''
            UPDATE submissions SET is_valid = FALSE WHERE player_id = ?
        ''', (discord_id,))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        conn.close()
        return False

def cancel_disqualification(discord_id: int) -> bool:
    """
    Снимает дисквалификацию с игрока и восстанавливает действительность его скриншотов.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    try:
        # Снимаем дисквалификацию
        cursor.execute('''
            UPDATE players SET is_disqualified = FALSE WHERE discord_id = ?
        ''', (discord_id,))
        
        # Восстанавливаем действительность скриншотов
        cursor.execute('''
            UPDATE submissions SET is_valid = TRUE WHERE player_id = ?
        ''', (discord_id,))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        conn.close()
        return False

def is_player_disqualified(discord_id: int) -> bool:
    """Проверяет, дисквалифицирован ли игрок."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT is_disqualified FROM players WHERE discord_id = ?
    ''', (discord_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return bool(result[0]) if result else False

def approve_screenshot(submission_id: int) -> bool:
    """Одобряет скриншот (устанавливает is_approved = TRUE)."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE submissions SET is_approved = TRUE WHERE submission_id = ?
        ''', (submission_id,))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except sqlite3.Error:
        conn.close()
        return False

def reject_screenshot(submission_id: int) -> bool:
    """Отклоняет скриншот (устанавливает is_approved = FALSE)."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE submissions SET is_approved = FALSE WHERE submission_id = ?
        ''', (submission_id,))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except sqlite3.Error:
        conn.close()
        return False

def get_approved_screenshots_stats() -> List[Tuple[int, str, str, int]]:
    """
    Возвращает статистику одобренных скриншотов для всех игроков.
    Возвращает список кортежей: (discord_id, nickname, static_id, approved_count)
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.discord_id, p.nickname, p.static_id, COUNT(s.submission_id) as approved_count
        FROM players p
        LEFT JOIN submissions s ON p.discord_id = s.player_id AND s.is_approved = TRUE AND s.is_valid = TRUE
        WHERE p.is_disqualified = FALSE
        GROUP BY p.discord_id, p.nickname, p.static_id
        HAVING approved_count > 0
        ORDER BY approved_count DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_submission_by_id(submission_id: int) -> Optional[dict]:
    """Получает данные скриншота по ID."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT submission_id, player_id, screenshot_url, submission_time, is_valid, is_approved
        FROM submissions WHERE submission_id = ?
    ''', (submission_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'submission_id': result[0],
            'discord_id': result[1],  # player_id это тот же discord_id
            'screenshot_url': result[2],
            'submission_time': result[3],
            'is_valid': result[4],
            'is_approved': result[5]
        }
    return None

def get_leaderboard_by_approved() -> List[Tuple[int, str, int, int]]:
    """
    Возвращает топ игроков по количеству одобренных скриншотов.
    Возвращает список кортежей: (discord_id, nickname, total_screenshots, approved_count)
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            p.discord_id, 
            p.nickname,
            COUNT(s.submission_id) as total_screenshots,
            COUNT(CASE WHEN s.is_approved = TRUE THEN 1 END) as approved_count
        FROM players p
        LEFT JOIN submissions s ON p.discord_id = s.player_id AND s.is_valid = TRUE
        WHERE p.is_disqualified = FALSE
        GROUP BY p.discord_id, p.nickname
        HAVING total_screenshots > 0
        ORDER BY approved_count DESC, total_screenshots DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_player_screenshot_number(discord_id: int, submission_id: int) -> int:
    """
    Возвращает личный номер скриншота игрока (1-й, 2-й, 3-й и т.д.).
    Основан на времени отправки скриншотов конкретного игрока.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Получаем порядковый номер скриншота среди всех скриншотов игрока
    cursor.execute('''
        SELECT COUNT(*) + 1 as screenshot_number
        FROM submissions s1
        WHERE s1.player_id = ? 
        AND s1.submission_time < (
            SELECT s2.submission_time 
            FROM submissions s2 
            WHERE s2.submission_id = ?
        )
    ''', (discord_id, submission_id))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else 1

def reset_all_statistics() -> bool:
    """
    Очищает все статистики и профили игроков (полный сброс для нового ивента).
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    try:
        # Удаляем все скриншоты
        cursor.execute("DELETE FROM submissions")
        
        # Удаляем всех игроков
        cursor.execute("DELETE FROM players")
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Ошибка при сбросе статистики: {e}")
        conn.close()
        return False
