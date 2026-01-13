"""
Планировщик напоминаний для пятничных отчетов
"""
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import ADMIN_ID, MANAGERS
import database as db

# Глобальные ссылки
_bot = None
_generate_json = None

async def send_report_reminder():
    """Отправить напоминание о сдаче отчета (пятница 14:00)"""
    if not _bot:
        return
    
    week, year = db.get_current_week()
    
    for username, dept_name in MANAGERS.items():
        dept = db.get_department_by_manager(username)
        if not dept:
            continue
        
        # Проверяем сдан ли уже отчет
        report = db.get_report(dept['id'], week, year)
        if report:
            continue  # Уже сдал
        
        print(f"📨 Напоминание для @{username} ({dept_name})")
        # TODO: Отправить сообщение руководителю когда будет user_id

async def send_nagging_reminder():
    """Напоминание для должников (пятница 17:00+)"""
    if not _bot:
        return
    
    missing = db.get_missing_reports()
    
    for dept in missing:
        print(f"⚠️ Напоминание (nagging) для @{dept['manager_username']}")
        # TODO: Отправить напоминание

async def send_admin_summary():
    """Отправить админу список должников (конец пятницы)"""
    if not _bot:
        return
    
    missing = db.get_missing_reports()
    
    if not missing:
        await _bot.send_message(ADMIN_ID, "✅ Все отделы сдали отчеты на этой неделе!")
    else:
        text = "⚠️ Не сдали отчет на этой неделе:\n\n"
        for dept in missing:
            text += f"• {dept['name']} (@{dept['manager_username']})\n"
        await _bot.send_message(ADMIN_ID, text)
    
    # Обновляем JSON после сводки
    if _generate_json:
        _generate_json()

def start_scheduler(bot, generate_json_func=None):
    """Запуск планировщика"""
    global _bot, _generate_json
    _bot = bot
    _generate_json = generate_json_func
    
    scheduler = AsyncIOScheduler()
    
    # Пятница 14:00 — первое напоминание
    scheduler.add_job(
        send_report_reminder,
        CronTrigger(day_of_week='fri', hour=14, minute=0),
        id='report_reminder'
    )
    
    # Пятница 17:00, 18:00, 19:00 — nagging
    for hour in [17, 18, 19]:
        scheduler.add_job(
            send_nagging_reminder,
            CronTrigger(day_of_week='fri', hour=hour, minute=0),
            id=f'nagging_{hour}'
        )
    
    # Пятница 20:00 — сводка админу
    scheduler.add_job(
        send_admin_summary,
        CronTrigger(day_of_week='fri', hour=20, minute=0),
        id='admin_summary'
    )
    
    scheduler.start()
    return scheduler
