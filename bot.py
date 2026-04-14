import os

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

QUIZ = 0

RIDDLES = [
    {
        "question": "Не лает, не кусает, а в дом не пускает.",
        "answers": {"замок"},
        "photo": "https://images.unsplash.com/photo-1517430816045-df4b7de11d1d",
    },
    {
        "question": "Сидит дед, во сто шуб одет. Кто его раздевает, тот слезы проливает.",
        "answers": {"лук"},
        "photo": "https://images.unsplash.com/photo-1587049633312-d628ae50a8ae",
    },
    {
        "question": "Без рук, без ног, а ворота открывает.",
        "answers": {"ветер"},
        "photo": "https://images.unsplash.com/photo-1500375592092-40eb2168fd21",
    },
    {
        "question": "Зимой и летом одним цветом.",
        "answers": {"ель", "елка"},
        "photo": "https://images.unsplash.com/photo-1510798831971-661eb04b3739",
    },
    {
        "question": "Что можно увидеть с закрытыми глазами?",
        "answers": {"сон", "сны"},
        "photo": "https://images.unsplash.com/photo-1511296265581-c2450046447d",
    },
]

SECRET = "Секретный ответ: ДОВЕРИЕ"
BTN_START = "▶️ Начать викторину"
BTN_HELP = "ℹ️ Помощь"
BTN_SKIP = "⏭ Пропустить"
BTN_CANCEL = "❌ Отмена"

MAIN_KB = ReplyKeyboardMarkup([[BTN_START, BTN_HELP]], resize_keyboard=True)
QUIZ_KB = ReplyKeyboardMarkup([[BTN_SKIP, BTN_CANCEL]], resize_keyboard=True)


def normalize_text(text: str) -> str:
    return text.strip().lower().replace("ё", "е")


async def send_riddle(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int) -> None:
    riddle = RIDDLES[index]
    text = f"Загадка {index + 1}/{len(RIDDLES)}:\n{riddle['question']}"
    photo = riddle.get("photo")
    if photo:
        await update.message.reply_photo(photo=photo, caption=text, reply_markup=QUIZ_KB)
    else:
        await update.message.reply_text(text, reply_markup=QUIZ_KB)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Привет! Я бот-викторина.\n"
        "Нажми кнопку «Начать викторину» или используй /start.",
        reply_markup=MAIN_KB,
    )
    return ConversationHandler.END


async def begin_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["riddle_index"] = 0
    context.user_data["in_quiz"] = True
    await update.message.reply_text("Поехали! Ответь на 5 загадок.")
    await send_riddle(update, context, 0)
    return QUIZ


async def handle_riddle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_text = normalize_text(update.message.text or "")
    index = context.user_data.get("riddle_index", 0)

    if index < 0 or index >= len(RIDDLES):
        await update.message.reply_text("Что-то пошло не так. Напиши /start, чтобы начать заново.")
        return ConversationHandler.END

    if user_text == normalize_text(BTN_CANCEL):
        return await cancel(update, context)

    if user_text == normalize_text(BTN_SKIP):
        index += 1
        context.user_data["riddle_index"] = index
        if index == len(RIDDLES):
            context.user_data["in_quiz"] = False
            context.user_data["skip_off_topic_once"] = True
            await update.message.reply_text(
                f"Ты пропустил(а) последнюю загадку.\n{SECRET}",
                reply_markup=MAIN_KB,
            )
            return ConversationHandler.END
        await update.message.reply_text("Ок, пропускаем. Следующая загадка:")
        await send_riddle(update, context, index)
        return QUIZ

    valid_answers = {normalize_text(answer) for answer in RIDDLES[index]["answers"]}
    if user_text in valid_answers:
        index += 1
        context.user_data["riddle_index"] = index

        if index == len(RIDDLES):
            context.user_data["in_quiz"] = False
            context.user_data["skip_off_topic_once"] = True
            await update.message.reply_text(f"Верно! {SECRET}", reply_markup=MAIN_KB)
            return ConversationHandler.END

        await update.message.reply_text("Верно!")
        await send_riddle(update, context, index)
        return QUIZ

    await update.message.reply_text("это не относится к нашей теме!")
    return QUIZ


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["in_quiz"] = False
    await update.message.reply_text(
        "Ок, остановили. Для новой игры: /start",
        reply_markup=MAIN_KB,
    )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Команды:\n"
        "/start — начать викторину\n"
        "/help — помощь\n"
        "/cancel — остановить игру\n\n"
        "Также можно использовать кнопки.",
        reply_markup=MAIN_KB,
    )
    return ConversationHandler.END


async def off_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("skip_off_topic_once", False):
        context.user_data["skip_off_topic_once"] = False
        return
    if context.user_data.get("in_quiz", False):
        return
    user_text = normalize_text(update.message.text or "")
    if user_text == normalize_text(BTN_START):
        await begin_quiz(update, context)
        return
    if user_text == normalize_text(BTN_HELP):
        await help_command(update, context)
        return
    await update.message.reply_text("это не относится к нашей теме!")


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("Не найден BOT_TOKEN в переменных окружения.")

    app = ApplicationBuilder().token(token).build()

    conversation = ConversationHandler(
        entry_points=[
            CommandHandler("start", begin_quiz),
            MessageHandler(filters.Regex(f"^{BTN_START}$"), begin_quiz),
        ],
        states={
            QUIZ: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_riddle)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex(f"^{BTN_CANCEL}$"), cancel),
        ],
    )

    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(conversation)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, off_topic),
        group=1,
    )

    app.run_polling()


if __name__ == "__main__":
    main()
