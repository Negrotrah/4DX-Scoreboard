import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton

from config import BOT_TOKEN, ADMIN_ID, MANAGERS, WEBAPP_URL, MAIN_GOAL_TARGET
import database as db
from scheduler import start_scheduler

# ============================================
# Инициализация
# ============================================
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ============================================
# Проверка ролей
# ============================================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def is_manager(username: str) -> bool:
    return username in MANAGERS if username else False

def get_manager_department(username: str) -> str:
    return MANAGERS.get(username, None) if username else None

# ============================================
# Команда /start
# ============================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    username = user.username
    
    # Супер-админ
    if is_admin(user.id):
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📊 Открыть табло", web_app=WebAppInfo(url=WEBAPP_URL))],
                [KeyboardButton(text="📝 Ввести выручку"), KeyboardButton(text="⚠️ Должники")],
                [KeyboardButton(text="✅ Заявки на доступ"), KeyboardButton(text="⚙️ Настройки")]
            ],
            resize_keyboard=True
        )
        await message.answer(
            f"👋 Добро пожаловать, Администратор!\n\n"
            f"Вы можете управлять системой отчетности.",
            reply_markup=keyboard
        )
        return
    
    # Руководитель отдела
    if is_manager(username):
        dept = get_manager_department(username)
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📊 Открыть табло", web_app=WebAppInfo(url=WEBAPP_URL))],
                [KeyboardButton(text="📝 Сдать отчет"), KeyboardButton(text="✏️ Исправить отчет")]
            ],
            resize_keyboard=True
        )
        await message.answer(
            f"👋 Добро пожаловать, руководитель!\n\n"
            f"📁 Ваш отдел: {dept}\n\n"
            f"Используйте кнопки ниже для работы.",
            reply_markup=keyboard
        )
        return
    
    # Проверяем одобренного наблюдателя
    if db.is_observer_approved(user.id):
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📊 Открыть табло", web_app=WebAppInfo(url=WEBAPP_URL))]
            ],
            resize_keyboard=True
        )
        await message.answer(
            f"👋 Добро пожаловать!\n\n"
            f"Вы можете просматривать табло.",
            reply_markup=keyboard
        )
        return
    
    # Новый пользователь — предлагаем подать заявку
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📨 Подать заявку на доступ")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        f"👋 Добро пожаловать!\n\n"
        f"Это закрытая система. Для доступа к табло подайте заявку.",
        reply_markup=keyboard
    )


# ============================================
# Заявка на доступ (Наблюдатели)
# ============================================
@dp.message(F.text == "📨 Подать заявку на доступ")
async def request_access(message: types.Message):
    user = message.from_user
    
    # Проверяем не одобрен ли уже
    if db.is_observer_approved(user.id):
        await message.answer("✅ Вы уже имеете доступ!")
        return
    
    # Сохраняем заявку
    db.request_access(user.id, user.username, user.first_name)
    
    await message.answer(
        "📨 Заявка отправлена!\n\n"
        "Ожидайте одобрения администратора."
    )
    
    # Уведомляем админа
    await bot.send_message(
        ADMIN_ID,
        f"📨 Новая заявка на доступ!\n\n"
        f"👤 {user.first_name} (@{user.username})\n"
        f"🆔 ID: {user.id}\n\n"
        f"Одобрить: /approve_{user.id}"
    )

# ============================================
# Админ: Одобрение заявок
# ============================================
@dp.message(F.text == "✅ Заявки на доступ")
async def show_pending(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    pending = db.get_pending_observers()
    
    if not pending:
        await message.answer("✅ Нет ожидающих заявок.")
        return
    
    text = "📋 Ожидающие заявки:\n\n"
    for obs in pending:
        text += f"• {obs['first_name']} (@{obs['username']})\n"
        text += f"  Одобрить: /approve_{obs['telegram_id']}\n\n"
    
    await message.answer(text)

@dp.message(F.text.startswith("/approve_"))
async def approve_user(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        user_id = int(message.text.split("_")[1])
        db.approve_observer(user_id)
        
        await message.answer(f"✅ Пользователь {user_id} одобрен!")
        
        # Уведомляем пользователя
        await bot.send_message(
            user_id,
            "🎉 Ваша заявка одобрена!\n\n"
            "Напишите /start чтобы получить доступ к табло."
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# ============================================
# Админ: Список должников
# ============================================
@dp.message(F.text == "⚠️ Должники")
async def show_debtors(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    missing = db.get_missing_reports()
    
    if not missing:
        await message.answer("✅ Все отделы сдали отчеты!")
        return
    
    text = "⚠️ Не сдали отчет на этой неделе:\n\n"
    for dept in missing:
        text += f"• {dept['name']} (@{dept['manager_username']})\n"
    
    await message.answer(text)

# ============================================
# Админ: Ввод выручки
# ============================================
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_revenue = State()
    # Настройки
    settings_menu = State()
    select_department = State()
    edit_dept_menu = State()
    edit_kvts_name = State()
    edit_kvts_target = State()
    edit_lead_name = State()
    edit_lead_plan = State()
    edit_manager = State()
    edit_main_goal_target = State()

@dp.message(F.text == "📝 Ввести выручку")
async def ask_revenue(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    current, previous = db.get_main_goal_history()
    
    await message.answer(
        f"💰 Текущая выручка: ${current:,}\n"
        f"📊 Прошлая неделя: ${previous:,}\n\n"
        f"Введите новую сумму выручки (число):"
    )
    await state.set_state(AdminStates.waiting_revenue)

@dp.message(AdminStates.waiting_revenue)
async def save_revenue(message: types.Message, state: FSMContext):
    try:
        value = int(message.text.replace(",", "").replace(" ", ""))
        db.update_main_goal(value, message.from_user.id)
        
        # Обновляем JSON для MiniApp
        generate_webapp_json()
        
        await message.answer(f"✅ Выручка обновлена: ${value:,}")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")


# ============================================
# Админ: Настройки (Админ-панель)
# ============================================
@dp.message(F.text == "⚙️ Настройки")
async def settings_menu(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📁 Настройки отделов")],
            [KeyboardButton(text="🎯 Изменить главную цель")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "⚙️ Настройки системы\n\n"
        "Выберите раздел:",
        reply_markup=keyboard
    )
    await state.set_state(AdminStates.settings_menu)

@dp.message(F.text == "🔙 Назад")
async def go_back(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.clear()
    await cmd_start(message)

@dp.message(F.text == "🎯 Изменить главную цель")
async def edit_main_goal(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        f"🎯 Текущая главная цель: ${MAIN_GOAL_TARGET:,}\n\n"
        f"Введите новую цель (число):\n"
        f"(Это изменит целевую сумму на табло)"
    )
    await state.set_state(AdminStates.edit_main_goal_target)

@dp.message(AdminStates.edit_main_goal_target)
async def save_main_goal_target(message: types.Message, state: FSMContext):
    try:
        value = int(message.text.replace(",", "").replace(" ", ""))
        
        # Обновляем в конфиге (в памяти)
        global MAIN_GOAL_TARGET
        from config import MAIN_GOAL
        MAIN_GOAL['target'] = value
        
        # Импортируем заново
        import config
        config.MAIN_GOAL_TARGET = value
        
        # Обновляем JSON
        generate_webapp_json()
        
        await message.answer(f"✅ Главная цель изменена: ${value:,}")
        await state.clear()
        await cmd_start(message)
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(F.text == "📁 Настройки отделов")
async def select_department(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    departments = db.get_all_departments()
    
    if not departments:
        await message.answer("❌ Отделы не найдены. Запустите бота заново.")
        return
    
    # Создаём кнопки для каждого отдела
    buttons = []
    for dept in departments:
        buttons.append([KeyboardButton(text=f"📁 {dept['name']}")])
    buttons.append([KeyboardButton(text="🔙 Назад")])
    
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    
    await message.answer(
        "📁 Выберите отдел для настройки:",
        reply_markup=keyboard
    )
    await state.set_state(AdminStates.select_department)

@dp.message(AdminStates.select_department)
async def show_department_settings(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await settings_menu(message, state)
        return
    
    # Извлекаем название отдела
    dept_name = message.text.replace("📁 ", "")
    
    # Ищем отдел
    departments = db.get_all_departments()
    dept = next((d for d in departments if d['name'] == dept_name), None)
    
    if not dept:
        await message.answer("❌ Отдел не найден")
        return
    
    await state.update_data(editing_dept=dept)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Название КВЦ"), KeyboardButton(text="🎯 Цель КВЦ")],
            [KeyboardButton(text="📈 Название показателя"), KeyboardButton(text="📊 План показателя")],
            [KeyboardButton(text="👤 Руководитель")],
            [KeyboardButton(text="🔙 К списку отделов")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        f"⚙️ Настройки отдела: {dept['name']}\n\n"
        f"👤 Руководитель: @{dept['manager_username']}\n"
        f"📈 Опережающий: {dept['lead_indicator_name']} (план: {dept['lead_indicator_plan']})\n"
        f"🎯 КВЦ: {dept['kvts_name']} (цель: {dept['kvts_target']})\n\n"
        f"Что изменить?",
        reply_markup=keyboard
    )
    await state.set_state(AdminStates.edit_dept_menu)

@dp.message(AdminStates.edit_dept_menu)
async def handle_dept_edit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    dept = data.get('editing_dept')
    
    if message.text == "🔙 К списку отделов":
        await select_department(message, state)
        return
    
    if message.text == "✏️ Название КВЦ":
        await message.answer(
            f"Текущее название КВЦ: {dept['kvts_name']}\n\n"
            f"Введите новое название:"
        )
        await state.set_state(AdminStates.edit_kvts_name)
    
    elif message.text == "🎯 Цель КВЦ":
        await message.answer(
            f"Текущая цель КВЦ: {dept['kvts_target']}\n\n"
            f"Введите новую цель (число):"
        )
        await state.set_state(AdminStates.edit_kvts_target)
    
    elif message.text == "📈 Название показателя":
        await message.answer(
            f"Текущее название: {dept['lead_indicator_name']}\n\n"
            f"Введите новое название:"
        )
        await state.set_state(AdminStates.edit_lead_name)
    
    elif message.text == "📊 План показателя":
        await message.answer(
            f"Текущий план: {dept['lead_indicator_plan']}\n\n"
            f"Введите новый план (число):"
        )
        await state.set_state(AdminStates.edit_lead_plan)
    
    elif message.text == "👤 Руководитель":
        await message.answer(
            f"Текущий руководитель: @{dept['manager_username']}\n\n"
            f"Введите username нового руководителя (без @):"
        )
        await state.set_state(AdminStates.edit_manager)

@dp.message(AdminStates.edit_kvts_name)
async def save_kvts_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    dept = data['editing_dept']
    
    db.update_department(dept['id'], kvts_name=message.text)
    generate_webapp_json()
    
    await message.answer(f"✅ Название КВЦ изменено: {message.text}")
    
    # Обновляем данные и возвращаемся
    dept['kvts_name'] = message.text
    await state.update_data(editing_dept=dept)
    await state.set_state(AdminStates.edit_dept_menu)
    await show_department_settings(message, state)

@dp.message(AdminStates.edit_kvts_target)
async def save_kvts_target(message: types.Message, state: FSMContext):
    try:
        value = int(message.text)
        data = await state.get_data()
        dept = data['editing_dept']
        
        db.update_department(dept['id'], kvts_target=value)
        generate_webapp_json()
        
        await message.answer(f"✅ Цель КВЦ изменена: {value}")
        
        dept['kvts_target'] = value
        await state.update_data(editing_dept=dept)
        await state.set_state(AdminStates.edit_dept_menu)
        
        # Показываем меню отдела заново
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✏️ Название КВЦ"), KeyboardButton(text="🎯 Цель КВЦ")],
                [KeyboardButton(text="📈 Название показателя"), KeyboardButton(text="📊 План показателя")],
                [KeyboardButton(text="👤 Руководитель")],
                [KeyboardButton(text="🔙 К списку отделов")]
            ],
            resize_keyboard=True
        )
        await message.answer("Что ещё изменить?", reply_markup=keyboard)
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(AdminStates.edit_lead_name)
async def save_lead_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    dept = data['editing_dept']
    
    db.update_department(dept['id'], lead_indicator_name=message.text)
    generate_webapp_json()
    
    await message.answer(f"✅ Название показателя изменено: {message.text}")
    
    dept['lead_indicator_name'] = message.text
    await state.update_data(editing_dept=dept)
    await state.set_state(AdminStates.edit_dept_menu)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Название КВЦ"), KeyboardButton(text="🎯 Цель КВЦ")],
            [KeyboardButton(text="📈 Название показателя"), KeyboardButton(text="📊 План показателя")],
            [KeyboardButton(text="👤 Руководитель")],
            [KeyboardButton(text="🔙 К списку отделов")]
        ],
        resize_keyboard=True
    )
    await message.answer("Что ещё изменить?", reply_markup=keyboard)

@dp.message(AdminStates.edit_lead_plan)
async def save_lead_plan(message: types.Message, state: FSMContext):
    try:
        value = int(message.text)
        data = await state.get_data()
        dept = data['editing_dept']
        
        db.update_department(dept['id'], lead_indicator_plan=value)
        generate_webapp_json()
        
        await message.answer(f"✅ План показателя изменён: {value}")
        
        dept['lead_indicator_plan'] = value
        await state.update_data(editing_dept=dept)
        await state.set_state(AdminStates.edit_dept_menu)
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✏️ Название КВЦ"), KeyboardButton(text="🎯 Цель КВЦ")],
                [KeyboardButton(text="📈 Название показателя"), KeyboardButton(text="📊 План показателя")],
                [KeyboardButton(text="👤 Руководитель")],
                [KeyboardButton(text="🔙 К списку отделов")]
            ],
            resize_keyboard=True
        )
        await message.answer("Что ещё изменить?", reply_markup=keyboard)
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(AdminStates.edit_manager)
async def save_manager(message: types.Message, state: FSMContext):
    data = await state.get_data()
    dept = data['editing_dept']
    
    username = message.text.replace("@", "").strip()
    
    db.update_department(dept['id'], manager_username=username)
    generate_webapp_json()
    
    await message.answer(f"✅ Руководитель изменён: @{username}")
    
    dept['manager_username'] = username
    await state.update_data(editing_dept=dept)
    await state.set_state(AdminStates.edit_dept_menu)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Название КВЦ"), KeyboardButton(text="🎯 Цель КВЦ")],
            [KeyboardButton(text="📈 Название показателя"), KeyboardButton(text="📊 План показателя")],
            [KeyboardButton(text="👤 Руководитель")],
            [KeyboardButton(text="🔙 К списку отделов")]
        ],
        resize_keyboard=True
    )
    await message.answer("Что ещё изменить?", reply_markup=keyboard)


# ============================================
# Руководители: Сдача отчета
# ============================================
class ReportStates(StatesGroup):
    waiting_lead_indicator = State()
    waiting_kvts = State()

@dp.message(F.text.in_(["📝 Сдать отчет", "✏️ Исправить отчет"]))
async def start_report(message: types.Message, state: FSMContext):
    username = message.from_user.username
    
    if not is_manager(username):
        await message.answer("❌ Вы не являетесь руководителем отдела.")
        return
    
    dept = db.get_department_by_manager(username)
    
    if not dept:
        # Создаём отдел если его нет
        dept_name = get_manager_department(username)
        dept_id = db.create_department(dept_name, username)
        dept = db.get_department_by_manager(username)
    
    await state.update_data(department=dept)
    
    await message.answer(
        f"📊 Отчет за текущую неделю\n"
        f"📁 Отдел: {dept['name']}\n\n"
        f"❓ Сколько «{dept['lead_indicator_name']}» выполнено за эту неделю?\n"
        f"(План: {dept['lead_indicator_plan']})"
    )
    await state.set_state(ReportStates.waiting_lead_indicator)

@dp.message(ReportStates.waiting_lead_indicator)
async def get_lead_indicator(message: types.Message, state: FSMContext):
    try:
        value = int(message.text)
        await state.update_data(lead_fact=value)
        
        data = await state.get_data()
        dept = data['department']
        
        await message.answer(
            f"✅ Принято: {value}\n\n"
            f"❓ Какой общий прогресс по «{dept['kvts_name']}»?\n"
            f"(Цель: {dept['kvts_target']})"
        )
        await state.set_state(ReportStates.waiting_kvts)
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(ReportStates.waiting_kvts)
async def get_kvts(message: types.Message, state: FSMContext):
    try:
        value = int(message.text)
        data = await state.get_data()
        dept = data['department']
        lead_fact = data['lead_fact']
        
        # Сохраняем отчет
        db.submit_report(dept['id'], lead_fact, value, message.from_user.id)
        
        # Обновляем JSON для MiniApp
        generate_webapp_json()
        
        await message.answer(
            f"✅ Отчет сохранен!\n\n"
            f"📁 Отдел: {dept['name']}\n"
            f"📈 {dept['lead_indicator_name']}: {lead_fact} / {dept['lead_indicator_plan']}\n"
            f"🎯 {dept['kvts_name']}: {value} / {dept['kvts_target']}\n\n"
            f"Спасибо за отчет! 🙏"
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите число!")

# ============================================
# Генерация JSON для MiniApp
# ============================================
WEBAPP_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'webapp', 'data.json')

def generate_webapp_json():
    """Генерирует JSON файл для MiniApp из базы данных"""
    week, year = db.get_current_week()
    prev_week, prev_year = db.get_previous_week()
    
    # Главная цель
    current_revenue, previous_revenue = db.get_main_goal_history()
    
    # Отделы
    departments = db.get_all_departments()
    dept_data = []
    
    for dept in departments:
        current_report, previous_report = db.get_current_and_previous_reports(dept['id'])
        
        dept_data.append({
            "id": dept['id'],
            "name": dept['name'],
            "leadIndicator": {
                "name": dept['lead_indicator_name'],
                "plan": dept['lead_indicator_plan'],
                "current": current_report['lead_indicator_fact'] if current_report else 0,
                "previous": previous_report['lead_indicator_fact'] if previous_report else 0
            },
            "kvts": {
                "name": dept['kvts_name'],
                "target": dept['kvts_target'],
                "current": current_report['kvts_progress'] if current_report else 0,
                "previous": previous_report['kvts_progress'] if previous_report else 0
            },
            "submitted": current_report is not None
        })
    
    data = {
        "mainGoal": {
            "target": MAIN_GOAL_TARGET,
            "current": current_revenue,
            "previous": previous_revenue
        },
        "week": week,
        "year": year,
        "departments": dept_data
    }
    
    # Сохраняем JSON
    os.makedirs(os.path.dirname(WEBAPP_DATA_PATH), exist_ok=True)
    with open(WEBAPP_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return data

# ============================================
# Запуск
# ============================================
async def main():
    # Инициализируем отделы из конфига
    for username, dept_name in MANAGERS.items():
        existing = db.get_department_by_manager(username)
        if not existing:
            db.create_department(dept_name, username)
            print(f"✅ Создан отдел: {dept_name} ({username})")
    
    # Генерируем начальный JSON
    generate_webapp_json()
    print("📊 JSON для MiniApp сгенерирован")
    
    # Запускаем планировщик
    start_scheduler(bot, generate_webapp_json)
    print("⏰ Планировщик запущен")
    
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
