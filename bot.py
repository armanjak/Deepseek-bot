from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

TELEGRAM_TOKEN = "8665201620:AAGw8uqyc-Svp-kUFxQVI3W_dMnktutFsUg"
DEEPSEEK_API_KEY = "sk-88be899f09e5408fbf298831030adf64"

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

memory = {}

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    user_text = update.message.text

    if user_id not in memory:
        memory[user_id] = [
            {
                "role": "system",
                "content": """
Ты спокойный уверенный жиган.
Говоришь коротко.
Без суеты.
Без пафоса.
Без фраз про ИИ.
Иногда используешь уличные обороты.
Но не превращайся в карикатуру.
"""
            }
        ]

    memory[user_id].append({
        "role": "user",
        "content": user_text
    })

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=memory[user_id]
    )

    ai_text = response.choices[0].message.content

    memory[user_id].append({
        "role": "assistant",
        "content": ai_text
    })

    await update.message.reply_text(ai_text)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

app.run_polling()
