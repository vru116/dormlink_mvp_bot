# bot/handlers.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from models import Listing
from datetime import datetime

TYPE, CATEGORY, DESCRIPTION, CONTACT = range(4)

DORMS = [
    "Общежитие №1", "Общежитие №2", "Общежитие №3",
    "Общежитие №4", "Общежитие №5", "Общежитие №6",
    "Общежитие №7", "Общежитие №8 «Трилистник»",
    "Общежитие №9", "Общежитие №10",
    "Дом аспиранта", "Студенческий городок Дубки"
]

ALLOWED_CATEGORIES = [
    "Книги", "Мебель", "Техника", "Одежда",
    "Аксессуары", "Спорт", "Еда",
    "Косметика", "Игры", "Другое"
]

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "dorm" in context.user_data:
        await update.message.reply_text(
            f"Вы уже выбрали: {context.user_data['dorm']}\n\n"
            "Команды:\n"
            "/add — создать объявление\n"
            "/list — посмотреть все\n"
            "/my — мои объявления\n"
            "/delete <id> — удалить своё\n"
            "/buy <id> — отметить как проданное\n"
            "/info — как пользоваться"
        )
        return

    keyboard = [
        [InlineKeyboardButton(d, callback_data=f"dorm_{d}")]
        for d in DORMS
    ]

    await update.message.reply_text(
        "Выберите общежитие:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def dorm_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    dorm = query.data.replace("dorm_", "")
    context.user_data["dorm"] = dorm

    await query.edit_message_text(
        f"Вы выбрали: {dorm}\n\n"
        "Команды:\n"
        "/add — создать\n"
        "/list — все объявления\n"
        "/my — мои объявления\n"
        "/delete <id> — удалить своё\n"
        "/buy <id> — отметить проданное\n"
        "/info — как пользоваться"
    )


# ================= ADD =================

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "dorm" not in context.user_data:
        await update.message.reply_text("Сначала /start")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("Продам", callback_data="type_Продам")],
        [InlineKeyboardButton("Куплю", callback_data="type_Куплю")],
    ]

    await update.message.reply_text(
        "Тип объявления:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return TYPE


async def type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    typ = query.data.replace("type_", "")
    context.user_data["type"] = typ

    keyboard = [
        [InlineKeyboardButton(c, callback_data=f"cat_{c}")]
        for c in ALLOWED_CATEGORIES
    ]

    await query.edit_message_text(
        f"Выбрано: {typ}\n\nВыберите категорию:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CATEGORY


async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cat = query.data.replace("cat_", "")
    context.user_data["category"] = cat

    await query.edit_message_text(
        f"Категория: {cat}\n\n"
        "Введите описание объявления\n"
        "(что именно, состояние, цена, где забрать и т.д.)"
    )

    return DESCRIPTION


async def add_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    if not desc:
        await update.message.reply_text("Описание не может быть пустым. Введите ещё раз:")
        return DESCRIPTION

    context.user_data["description"] = desc

    await update.message.reply_text(
        "Укажите контакт для связи\n"
        "(лучше всего @username в Telegram)"
    )

    return CONTACT


async def add_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.text.strip()
    if not contact:
        await update.message.reply_text("Контакт не может быть пустым. Введите ещё раз:")
        return CONTACT

    Listing.create(
        author_id=update.effective_user.id,
        dorm=context.user_data["dorm"],
        type=context.user_data["type"],
        category=context.user_data["category"],
        description=context.user_data["description"],
        contact=contact,
    )

    await update.message.reply_text(
        "✅ Объявление успешно добавлено!\n"
        "Посмотреть все: /list\n"
        "Посмотреть свои: /my"
    )

    # Очищаем ТОЛЬКО временные ключи объявления
    # НЕ трогаем "dorm"!
    context.user_data.pop("type", None)
    context.user_data.pop("category", None)
    context.user_data.pop("description", None)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добавление отменено.")

    # Очищаем только временные ключи
    context.user_data.pop("type", None)
    context.user_data.pop("category", None)
    context.user_data.pop("description", None)

    return ConversationHandler.END


# ================= MY ADS / MY =================

async def my_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "dorm" not in context.user_data:
        await update.message.reply_text("Сначала выберите общежитие: /start")
        return

    user_id = update.effective_user.id
    dorm = context.user_data["dorm"]

    listings = Listing.select().where(
        Listing.author_id == user_id,
        Listing.dorm == dorm,
        Listing.status == "активно"
    ).order_by(Listing.created_at.desc())

    if not listings.exists():
        await update.message.reply_text("У вас нет активных объявлений в этом общежитии.")
        return

    await update.message.reply_text(f"Ваши объявления в {dorm}:\n")

    for l in listings[:10]:
        created = l.created_at.strftime("%d.%m %H:%M")
        text = (
            f"#{l.id}  {l.type.upper()} | {l.category}\n"
            f"{l.description}\n"
            f"Контакт: {l.contact}\n"
            f"Добавлено: {created}\n"
            "──────────────────────"
        )
        await update.message.reply_text(text)

    await update.message.reply_text("Удалить объявление: /delete <номер>")


# ================= LIST =================

async def list_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "dorm" not in context.user_data:
        await update.message.reply_text("Сначала выберите общежитие: /start")
        return

    listings = Listing.select().where(
        Listing.dorm == context.user_data["dorm"],
        Listing.status == "активно"
    ).order_by(Listing.created_at.desc())

    if not listings.exists():
        await update.message.reply_text("В вашем общежитии пока нет активных объявлений.")
        return

    await update.message.reply_text(f"Активные объявления в {context.user_data['dorm']}:\n")

    for l in listings[:10]:
        created = l.created_at.strftime("%d.%m %H:%M")
        text = (
            f"#{l.id}  {l.type.upper()} | {l.category}\n"
            f"{l.description}\n"
            f"Контакт: {l.contact}\n"
            f"Добавлено: {created}\n"
            "──────────────────────"
        )
        await update.message.reply_text(text)


# ================= DELETE =================

async def delete_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "dorm" not in context.user_data:
        await update.message.reply_text("Сначала выберите общежитие: /start")
        return

    if not context.args:
        # Показываем список своих объявлений
        await my_ads(update, context)
        return

    try:
        lid = int(context.args[0])
        l = Listing.get(
            Listing.id == lid,
            Listing.author_id == update.effective_user.id,
            Listing.dorm == context.user_data["dorm"],
            Listing.status == "активно"
        )
        l.delete_instance()
        await update.message.reply_text(f"Объявление #{lid} удалено.")
    except Listing.DoesNotExist:
        await update.message.reply_text("Объявление не найдено, уже удалено или не ваше.")


# ================= BUY =================

async def buy_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "dorm" not in context.user_data:
        await update.message.reply_text("Сначала выберите общежитие: /start")
        return

    if not context.args:
        await update.message.reply_text("Пример: /buy 3")
        return

    try:
        lid = int(context.args[0])
        l = Listing.get(
            Listing.id == lid,
            Listing.author_id == update.effective_user.id,
            Listing.dorm == context.user_data["dorm"],
            Listing.status == "активно"
        )
        l.status = "продано"
        l.save()
        await update.message.reply_text(f"Ваше объявление #{lid} отмечено как проданное.")
    except Listing.DoesNotExist:
        await update.message.reply_text("Объявление не найдено, уже продано или не ваше.")


# ================= INFO / HELP =================

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Как пользоваться DormLink:\n\n"
        "1. Выберите общежитие\n"
        "   /start → нажмите на своё общежитие\n\n"
        "2. Создать объявление\n"
        "   /add → выберите «Продам» или «Куплю» → категорию → описание → контакт\n\n"
        "3. Посмотреть объявления\n"
        "   /list — все активные в вашем общежитии\n"
        "   /my — только ваши объявления\n\n"
        "4. Управление\n"
        "   /delete <номер> — удалить своё объявление\n"
        "   /buy <номер> — отметить своё как проданное\n\n"
        "5. Отмена\n"
        "   /cancel — в любой момент создания объявления\n\n"
        "Готовы? Напишите /start!"
    )

    await update.message.reply_text(text)