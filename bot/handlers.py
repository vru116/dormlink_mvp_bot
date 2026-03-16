from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler

from models import Listing
from datetime import datetime

from telegram import ReplyKeyboardMarkup, KeyboardButton


TYPE, CATEGORY, DESCRIPTION, CONTACT, PHOTO = range(5)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "dorm" in context.user_data:
        await update.message.reply_text(
            f"Вы уже выбрали: {context.user_data['dorm']}"
        )

        await send_menu(update, context)


        return

    keyboard = [[InlineKeyboardButton(d, callback_data=f"dorm_{d}")] for d in DORMS]
    await update.message.reply_text("Выберите общежитие:", reply_markup=InlineKeyboardMarkup(keyboard))


async def change_dorm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton(d, callback_data=f"dorm_{d}")]
        for d in DORMS
    ]

    await update.message.reply_text(
        "Выберите новое общежитие:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )



async def dorm_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dorm = query.data.replace("dorm_", "")
    context.user_data["dorm"] = dorm
    await query.edit_message_text(
        f"Вы выбрали: {dorm}"
    )

    await send_menu(update, context)



async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "dorm" not in context.user_data:
        await update.message.reply_text("Сначала /start")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("Продам", callback_data="type_Продам")],
        [InlineKeyboardButton("Куплю", callback_data="type_Куплю")],
    ]
    await update.message.reply_text("Тип объявления:", reply_markup=InlineKeyboardMarkup(keyboard))
    return TYPE


async def type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    typ = query.data.replace("type_", "")
    context.user_data["type"] = typ

    keyboard = [[InlineKeyboardButton(c, callback_data=f"cat_{c}")] for c in ALLOWED_CATEGORIES]
    await query.edit_message_text(f"Выбрано: {typ}\n\nВыберите категорию:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CATEGORY


async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data.replace("cat_", "")
    context.user_data["category"] = cat

    await query.edit_message_text(f"Категория: {cat}\n\nВведите описание объявления\n(что именно, состояние, цена, где забрать и т.д.)")
    return DESCRIPTION


async def add_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    if not desc:
        await update.message.reply_text("Описание не может быть пустым. Введите ещё раз:")
        return DESCRIPTION

    context.user_data["description"] = desc
    await update.message.reply_text("Укажите контакт для связи\n(лучше всего @username в Telegram)")
    return CONTACT


async def add_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.text.strip()
    if not contact:
        await update.message.reply_text("Контакт не может быть пустым. Введите ещё раз:")
        return CONTACT

    context.user_data["contact"] = contact

    keyboard = [[InlineKeyboardButton("Пропустить фото", callback_data="skip_photo")]]
    await update.message.reply_text(
        "Хотите прикрепить фото?\nОтправьте фото или нажмите кнопку:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PHOTO


async def add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    photo_file_id = None
    photo_type = None

    # ---------- skip кнопка ----------
    if update.callback_query:
        query = update.callback_query
        await query.answer()

        if query.data == "skip_photo":
            await query.edit_message_text("Фото пропущено")

            dorm = context.user_data.get("dorm")

            Listing.create(
                author_id=update.effective_user.id,
                dorm=dorm,
                type=context.user_data["type"],
                category=context.user_data["category"],
                description=context.user_data["description"],
                contact=context.user_data["contact"],
                photo_file_id=None,
                photo_type=None,
            )

            await query.message.reply_text("Объявление создано")

            await send_menu(update, context)

            context.user_data.clear()
            if dorm:
                context.user_data["dorm"] = dorm

            return ConversationHandler.END


    # ---------- текст skip ----------
    elif update.message and update.message.text:
        txt = update.message.text.lower()
        if txt in ["skip", "/skip", "пропустить"]:
            dorm = context.user_data.get("dorm")
            Listing.create(
                author_id=update.effective_user.id,
                dorm=dorm,
                type=context.user_data["type"],
                category=context.user_data["category"],
                description=context.user_data["description"],
                contact=context.user_data["contact"],
                photo_file_id=None,
                photo_type=None,
            )

            await update.message.reply_text("Фото пропущено")
            await update.message.reply_text("Объявление создано")

            await send_menu(update, context)


            context.user_data.clear()
            if dorm:
                context.user_data["dorm"] = dorm

            return ConversationHandler.END
        else:
            await update.message.reply_text(
                "Отправьте фото или нажмите Пропустить"
            )
            return PHOTO

    # ---------- фото ----------
    elif update.message and update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
        photo_type = "photo"
        await update.message.reply_text("Фото добавлено")

    # ---------- документ ----------
    elif update.message and update.message.document:
        doc = update.message.document
        mime = doc.mime_type
        if mime in ["image/png", "image/jpeg", "image/webp"]:
            photo_file_id = doc.file_id
            photo_type = "document"
            await update.message.reply_text("Фото добавлено")
        else:
            await update.message.reply_text(
                "Это не изображение\nНужно PNG / JPG / WEBP"
            )
            return PHOTO

    else:
        await update.message.reply_text("Нужна фотография")
        return PHOTO

    # ---------- сохранение фото ----------
    Listing.create(
        author_id=update.effective_user.id,
        dorm=context.user_data["dorm"],
        type=context.user_data["type"],
        category=context.user_data["category"],
        description=context.user_data["description"],
        contact=context.user_data["contact"],
        photo_file_id=photo_file_id,
        photo_type=photo_type,
    )

    await update.message.reply_text("Объявление создано")

    await send_menu(update, context)


    dorm = context.user_data.get("dorm")
    context.user_data.clear()
    if dorm:
        context.user_data["dorm"] = dorm

    return ConversationHandler.END



async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добавление отменено.")
    for key in ["type", "category", "description", "contact", "photo_file_id"]:
        context.user_data.pop(key, None)
    return ConversationHandler.END

# ================= MY ADS =================

async def my_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "dorm" not in context.user_data:
        await update.message.reply_text("Сначала /start")
        return

    user_id = update.effective_user.id
    dorm = context.user_data["dorm"]

    listings = Listing.select().where(
        Listing.author_id == user_id,
        Listing.dorm == dorm,
        Listing.status == "активно"
    ).order_by(Listing.created_at.desc())

    if not listings.exists():
        await update.message.reply_text("У вас нет активных объявлений.")
        return

    await update.message.reply_text(f"Ваши объявления в {dorm}:\n")

    for l in listings[:8]:
        created = l.created_at.strftime("%d.%m %H:%M")
        text = (
            f"#{l.id}  {l.type.upper()} | {l.category}\n"
            f"{l.description}\n"
            f"Контакт: {l.contact}\n"
            f"Добавлено: {created}"
        )

        if l.photo_file_id:
            if l.photo_type == "photo":
                await update.message.reply_photo(
                    photo=l.photo_file_id,
                    caption=text
                )
            else:
                await update.message.reply_document(
                    document=l.photo_file_id,
                    caption=text
                )

        else:
            await update.message.reply_text(text + "\n(без фото)")

        
    await send_menu(update, context)




# ================= LIST =================

async def list_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "dorm" not in context.user_data:
        await update.message.reply_text("Сначала /start")
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
            f"Добавлено: {created}"
        )

        if l.photo_file_id:
            if l.photo_type == "photo":
                await update.message.reply_photo(photo=l.photo_file_id, caption=text)
            else:  # document
                await update.message.reply_document(document=l.photo_file_id, caption=text)
        else:
            await update.message.reply_text(text + "\n(без фото)")

    await send_menu(update, context)




# ================= DELETE =================

async def delete_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "dorm" not in context.user_data:
        await update.message.reply_text("Сначала /start")
        return

    if not context.args:
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
        await send_menu(update, context)

    except Listing.DoesNotExist:
        await update.message.reply_text("Не найдено, уже удалено или не ваше.")


# ================= BUY =================

async def buy_listing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "dorm" not in context.user_data:
        await update.message.reply_text("Сначала /start")
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
        await update.message.reply_text(f"Ваше объявление #{lid} отмечено как проданное/купленное.")
    except Listing.DoesNotExist:
        await update.message.reply_text("Не найдено, уже продано или не ваше.")

    await send_menu(update, context)



async def send_menu(update, context):

    keyboard = [
        [KeyboardButton("➕ Создать"), KeyboardButton("📋 Все")],
        [KeyboardButton("👤 Мои"), KeyboardButton("♻ Сменить общагу")],
        [KeyboardButton("ℹ Помощь")],
    ]

    markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


    text = "Выберите действие:"

    if update.message:
        await update.message.reply_text(text, reply_markup=markup)

    elif update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=markup)

async def menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "➕ Создать":
        return await add_start(update, context)

    elif text == "📋 Все":
        return await list_listings(update, context)

    elif text == "👤 Мои":
        return await my_ads(update, context)

    elif text == "♻ Сменить общагу":
        return await change_dorm(update, context)

    elif text == "ℹ Помощь":
        return await info_command(update, context)



# ================= INFO =================

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Как пользоваться DormLink:\n\n"
        "1. /start — выбрать общежитие\n"
        "2. /add — создать объявление (можно с фото)\n"
        "   - после описания и контакта можно прикрепить фото\n"
        "   - или пропустить (кнопка /skip)\n"
        "3. /list — все объявления в общаге\n"
        "4. /my — только ваши\n"
        "5. /delete <id> — удалить своё\n"
        "6. /buy <id> — отметить своё как проданное\n"
        "7. /cancel — отменить создание\n\n"
        "Готовы? /start!"
    )
    await update.message.reply_text(text)

    await send_menu(update, context)
