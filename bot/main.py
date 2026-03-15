# bot/main.py

import os
from dotenv import load_dotenv

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from handlers import (
    start, dorm_chosen,
    add_start, type_selected, category_selected,
    add_description, add_contact, add_photo, cancel,
    list_listings, my_ads, delete_listing, buy_listing,
    info_command, change_dorm
)

from models import db, Listing

TYPE, CATEGORY, DESCRIPTION, CONTACT, PHOTO = range(5)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN не найден в .env!")

def main():
    db.connect()
    db.create_tables([Listing], safe=True)
    print("База данных готова")

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            TYPE: [CallbackQueryHandler(type_selected, pattern="^type_")],
            CATEGORY: [CallbackQueryHandler(category_selected, pattern="^cat_")],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_contact)],
            PHOTO: [
                MessageHandler(filters.PHOTO, add_photo),
                MessageHandler(filters.Document.ALL, add_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_photo),
                CallbackQueryHandler(add_photo, pattern="^skip_photo$"),
            ],

        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(dorm_chosen, pattern="^dorm_"))
    app.add_handler(CommandHandler("change", change_dorm))


    app.add_handler(conv)

    app.add_handler(CommandHandler("list", list_listings))
    app.add_handler(CommandHandler("my", my_ads))
    app.add_handler(CommandHandler("delete", delete_listing))
    app.add_handler(CommandHandler("buy", buy_listing))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("help", info_command))

    print("Бот запущен. Ctrl+C — остановка")
    app.run_polling(allowed_updates=["message", "callback_query"], drop_pending_updates=True)


if __name__ == "__main__":
    main()