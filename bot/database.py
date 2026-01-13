import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'scoreboard.db')

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    """Инициализация базы данных"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица отделов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            manager_username TEXT,
            kvts_name TEXT DEFAULT 'КВЦ',
            kvts_target INTEGER DEFAULT 100,
            kvts_deadline DATE,
            lead_indicator_name TEXT DEFAULT 'Показатель',
            lead_indicator_plan INTEGER DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица еженедельных отчетов (историчность!)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_id INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            year INTEGER NOT NULL,
            lead_indicator_fact INTEGER DEFAULT 0,
            kvts_progress INTEGER DEFAULT 0,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            submitted_by INTEGER,
            FOREIGN KEY (department_id) REFERENCES departments(id),
            UNIQUE(department_id, week_number, year)
        )
    ''')
    
    # Таблица главной цели (историчность!)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS main_goal_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_number INTEGER NOT NULL,
            year INTEGER NOT NULL,
            current_value INTEGER DEFAULT 0,
            target_value INTEGER DEFAULT 1000000,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER,
            UNIQUE(week_number, year)
        )
    ''')
    
    # Таблица наблюдателей (белый список)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS observers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            approved INTEGER DEFAULT 0,
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_current_week() -> tuple:
    """Возвращает (номер_недели, год)"""
    now = datetime.now()
    return now.isocalendar()[1], now.year

def get_previous_week() -> tuple:
    """Возвращает (номер_недели, год) прошлой недели"""
    now = datetime.now() - timedelta(weeks=1)
    return now.isocalendar()[1], now.year


# ============================================
# Операции с отделами
# ============================================

def get_all_departments() -> List[Dict]:
    """Получить все отделы"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM departments ORDER BY id')
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

def get_department_by_manager(username: str) -> Optional[Dict]:
    """Получить отдел по username руководителя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM departments WHERE manager_username = ?', (username,))
    columns = [desc[0] for desc in cursor.description]
    row = cursor.fetchone()
    conn.close()
    return dict(zip(columns, row)) if row else None

def create_department(name: str, manager_username: str) -> int:
    """Создать отдел"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO departments (name, manager_username)
        VALUES (?, ?)
    ''', (name, manager_username))
    conn.commit()
    dept_id = cursor.lastrowid
    conn.close()
    return dept_id

def update_department(dept_id: int, **kwargs):
    """Обновить настройки отдела"""
    conn = get_connection()
    cursor = conn.cursor()
    
    allowed_fields = ['name', 'manager_username', 'kvts_name', 'kvts_target', 
                      'kvts_deadline', 'lead_indicator_name', 'lead_indicator_plan']
    
    updates = []
    values = []
    for key, value in kwargs.items():
        if key in allowed_fields:
            updates.append(f'{key} = ?')
            values.append(value)
    
    if updates:
        values.append(dept_id)
        cursor.execute(f'''
            UPDATE departments SET {', '.join(updates)} WHERE id = ?
        ''', values)
        conn.commit()
    
    conn.close()

# ============================================
# Операции с отчетами
# ============================================

def submit_report(department_id: int, lead_fact: int, kvts_progress: int, user_id: int):
    """Сохранить еженедельный отчет (INSERT, не UPDATE!)"""
    week, year = get_current_week()
    conn = get_connection()
    cursor = conn.cursor()
    
    # Используем INSERT OR REPLACE для текущей недели
    cursor.execute('''
        INSERT OR REPLACE INTO weekly_reports 
        (department_id, week_number, year, lead_indicator_fact, kvts_progress, submitted_by)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (department_id, week, year, lead_fact, kvts_progress, user_id))
    
    conn.commit()
    conn.close()

def get_report(department_id: int, week: int, year: int) -> Optional[Dict]:
    """Получить отчет за конкретную неделю"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM weekly_reports 
        WHERE department_id = ? AND week_number = ? AND year = ?
    ''', (department_id, week, year))
    columns = [desc[0] for desc in cursor.description]
    row = cursor.fetchone()
    conn.close()
    return dict(zip(columns, row)) if row else None

def get_current_and_previous_reports(department_id: int) -> tuple:
    """Получить отчеты текущей и прошлой недели"""
    current_week, current_year = get_current_week()
    prev_week, prev_year = get_previous_week()
    
    current = get_report(department_id, current_week, current_year)
    previous = get_report(department_id, prev_week, prev_year)
    
    return current, previous

def get_missing_reports() -> List[Dict]:
    """Получить список отделов, не сдавших отчет на этой неделе"""
    week, year = get_current_week()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT d.* FROM departments d
        LEFT JOIN weekly_reports r 
            ON d.id = r.department_id 
            AND r.week_number = ? 
            AND r.year = ?
        WHERE r.id IS NULL
    ''', (week, year))
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

# ============================================
# Главная цель
# ============================================

def update_main_goal(value: int, user_id: int):
    """Обновить главную цель (с историчностью)"""
    week, year = get_current_week()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO main_goal_history 
        (week_number, year, current_value, updated_by)
        VALUES (?, ?, ?, ?)
    ''', (week, year, value, user_id))
    
    conn.commit()
    conn.close()

def get_main_goal_history() -> tuple:
    """Получить текущее и прошлое значение главной цели"""
    current_week, current_year = get_current_week()
    prev_week, prev_year = get_previous_week()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT current_value FROM main_goal_history 
        WHERE week_number = ? AND year = ?
    ''', (current_week, current_year))
    current = cursor.fetchone()
    
    cursor.execute('''
        SELECT current_value FROM main_goal_history 
        WHERE week_number = ? AND year = ?
    ''', (prev_week, prev_year))
    previous = cursor.fetchone()
    
    conn.close()
    
    return (current[0] if current else 0, previous[0] if previous else 0)

# ============================================
# Наблюдатели
# ============================================

def request_access(telegram_id: int, username: str, first_name: str):
    """Запрос на доступ"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO observers (telegram_id, username, first_name)
        VALUES (?, ?, ?)
    ''', (telegram_id, username, first_name))
    conn.commit()
    conn.close()

def approve_observer(telegram_id: int):
    """Одобрить наблюдателя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE observers SET approved = 1, approved_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
    ''', (telegram_id,))
    conn.commit()
    conn.close()

def is_observer_approved(telegram_id: int) -> bool:
    """Проверить одобрен ли наблюдатель"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT approved FROM observers WHERE telegram_id = ?', (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] == 1 if row else False

def get_pending_observers() -> List[Dict]:
    """Получить список ожидающих одобрения"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM observers WHERE approved = 0')
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

# Инициализация при импорте
init_db()
