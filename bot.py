from flask import Flask
from threading import Thread
import json
import os

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes
)

from openai import OpenAI
import traceback

TELEGRAM_TOKEN = "8665201620:AAGw8uqyc-Svp-kUFxQVI3W_dMnktutFsUg"
DEEPSEEK_API_KEY = "sk-88be899f09e5408fbf298831030adf64"

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

MEMORY_FILE = "memory.json"
ADMIN_ID = 315356999

# загрузка памяти

if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = {}

# flask keepalive для render

app_web = Flask("")

@app_web.route("/")
def home():
    return "братишка в теме"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

Thread(target=run_web, daemon=True).start()

# системный prompt

SYSTEM_PROMPT = """
Ты спокойный уверенный жиган.
Говоришь коротко.
Без суеты.
Без пафоса.
Без фраз про ИИ.
Не скатывайся в клоунаду кидаясь неуместными жаргонными словами.
Не стесняйся в выражениях.
Можно иногда пошутить.
обращаться к пользователю помимо обычных слов можно: старичок, братислав, бротуль
"""

# отправка memory.json админу

async def send_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    with open(MEMORY_FILE, "rb") as f:
        await update.message.reply_document(f)

# reset памяти

async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.chat_id)

    memory[user_id] = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

    await update.message.reply_text("Память очищена.")

# основной reply handler

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.message.chat_id)
    user_text = update.message.text

    # создаем память новому пользователю

    if user_id not in memory:
        memory[user_id] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

    # сообщение пользователя

    memory[user_id].append({
        "role": "user",
        "content": user_text
    })

    # запрос к deepseek

    try:
        response = client.chat.completions.create(
        model="deepseek-chat",
        messages=memory[user_id]
        )

        ai_text = response.choices[0].message.content

        memory[user_id].append({
        "role": "assistant",
        "content": ai_text
        })

    # ограничение памяти
    if user_id != str(ADMIN_ID):
        system_prompt = memory[user_id][0]
        chat_history = memory[user_id][1:]

        # оставляем последние 15 сообщений
        chat_history = chat_history[-15:]

        memory[user_id] = [system_prompt] + chat_history

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(ai_text)

except Exception as e:
    print("ОШИБКА:")
    print(traceback.format_exc())

    await update.message.reply_text(
        "Братух, чет поплохело. Попробуй еще раз."
    )


# запуск telegram

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("memory", send_memory))
app.add_handler(CommandHandler("reset", reset_memory))

app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, reply)
)

print("поехали")

app.run_polling(
    drop_pending_updates=True,
    allowed_updates=Update.ALL_TYPES
)
