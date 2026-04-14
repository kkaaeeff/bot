import os

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

Q1, Q2, Q3, Q4, Q5 = range(5)

RIDDLES = [
    ("Не лает, не кусает, а в дом не пускает.", {"замок"}),
    ("Сидит дед, во сто шуб одет. Кто его раздевает, тот слезы проливает.", {"лук"}),
    ("Без рук, без ног, а ворота открывает.", {"ветер"}),
    ("Зимой и летом одним цветом.", {"ель", "елка"}),
    ("Что можно увидеть с закрытыми глазами?", {"сон", "сны"}),
]

SECRET = "Секретный ответ: ДОВЕРИЕ"


def normalize_text(text: str) -> str:
    return text.strip().lower().replace("ё", "е")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["riddle_index"] = 0
    context.user_data["in_quiz"] = True
    await update.message.reply_text(
        "Привет! Ответь на 5 загадок.\n\n"
        f"Загадка 1: {RIDDLES[0][0]}"
    )
    return Q1


async def handle_riddle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_text = normalize_text(update.message.text or "")
    index = context.user_data.get("riddle_index", 0)

    if index < 0 or index >= len(RIDDLES):
        await update.message.reply_text("Что-то пошло не так. Напиши /start, чтобы начать заново.")
        return ConversationHandler.END

    valid_answers = {normalize_text(answer) for answer in RIDDLES[index][1]}

    if user_text in valid_answers:
        index += 1
        context.user_data["riddle_index"] = index

        if index == len(RIDDLES):
            context.user_data["in_quiz"] = False
            await update.message.reply_text(f"Верно! {SECRET}")
            return ConversationHandler.END

        await update.message.reply_text(f"Верно!\nЗагадка {index + 1}: {RIDDLES[index][0]}")
        return index

    await update.message.reply_text("это не относится к нашей теме!")
    return index


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["in_quiz"] = False
    await update.message.reply_text("Ок, остановили. Для новой игры: /start")
    return ConversationHandler.END


async def off_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("in_quiz", False):
        return
    await update.message.reply_text("это не относится к нашей теме!")


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("Не найден BOT_TOKEN в переменных окружения.")

    app = ApplicationBuilder().token(token).build()

    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            Q1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_riddle)],
            Q2: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_riddle)],
            Q3: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_riddle)],
            Q4: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_riddle)],
            Q5: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_riddle)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conversation)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, off_topic),
        group=1,
    )

    app.run_polling()


if __name__ == "__main__":
    main()
