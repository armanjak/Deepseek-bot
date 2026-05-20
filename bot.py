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
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

TELEGRAM_TOKEN = "8665201620:AAGw8uqyc-Svp-kUFxQVI3W_dMnktutFsUg"
DEEPSEEK_API_KEY = "sk-88be899f09e5408fbf298831030adf64"

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

MEMORY_FILE = "memory.json"
ADMIN_ID = 315356999

if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = {}

app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is alive"

def run_web():
    app_web.run(host='0.0.0.0', port=10000)

Thread(target=run_web).start()

async def send_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    with open(MEMORY_FILE, "rb") as f:
        await update.message.reply_document(f)
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.chat_id)
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
Не скатывайся в клоунаду кидаясь не уместными жаргонными словами.
Не стесняйся в выражениях.
Можно иногда пошутить.
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

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

    await update.message.reply_text(ai_text)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("memory", send_memory))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

app.run_polling(drop_pending_updates=True)
