# ============================================
# Конфигурация бота
# ============================================

BOT_TOKEN = "8331119114:AAEBpEEX4kzricpIDk9YAQNyeJzV8MipJiw"

# Супер-админ (COO) — Telegram ID
ADMIN_ID = 1435120359  # Твой ID

# Руководители отделов — username -> отдел
MANAGERS = {
    "manager1_username": "Отдел продаж",
    "manager2_username": "Отдел маркетинга",
    "manager3_username": "Отдел разработки",
    "manager4_username": "Отдел поддержки",
    "manager5_username": "Отдел HR",
    "manager6_username": "Отдел финансов",
    "manager7_username": "Отдел логистики",
    "manager8_username": "Отдел закупок",
}

# Время отправки напоминаний (пятница)
REPORT_TIME = "14:00"
REMINDER_TIME = "17:00"

# Главная цель компании
MAIN_GOAL = {
    "name": "Выручка",
    "target": 1_000_000,
    "currency": "$"
}
MAIN_GOAL_TARGET = 1_000_000  # Для удобства импорта

# URL Mini App (после деплоя на GitHub Pages)
WEBAPP_URL = "https://username.github.io/4dx-scoreboard/"
