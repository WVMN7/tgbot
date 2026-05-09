
import logging
import asyncio
from datetime import time
import pytz
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from telegram.request import HTTPXRequest

# ===================== SOZLAMALAR =====================
BOT_TOKEN = "8007572675:AAEpXtwxgLBvJp6jkjqAYrs2SvDiYpUwT5M"
VIDEO_LINK = "https://youtu.be/C8fHOcCHnf8"

# 10 daqiqadan keyin (yoki test uchun 10 soniyadan keyin) yuboriladigan GOLOS fayli
# Fayl .ogg yoki .mp3 formatida bo'lishi mumkin
DELAYED_VOICE = "./audio_2026-05-09_10-51-40.ogg" 

# Test uchun 10 soniya (keyinchalik 600 qilib qo'ying)
DELAY_SECONDS = 10 

SCHEDULED_HOUR = 9
SCHEDULED_MINUTE = 0
TIMEZONE = pytz.timezone("Asia/Tashkent")

user_ids = set()
# ======================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

async def send_delayed_voice_msg(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Belgilangan vaqtdan keyin ovozli xabar (golos) yuboradi"""
    chat_id = context.job.data
    logger.info(f"Vaqt keldi! Chat: {chat_id} ga golos yuborilmoqda...")

    if not os.path.exists(DELAYED_VOICE):
        logger.error(f"Ovozli fayl topilmadi: {DELAYED_VOICE}")
        return

    try:
        with open(DELAYED_VOICE, "rb") as f:
            await context.bot.send_voice(
                chat_id=chat_id,
                voice=f,
                # caption="🔊 Bu sizga va'da qilingan ovozli xabar!",
                read_timeout=60,
                write_timeout=60
            )
        logger.info(f"Golos muvaffaqiyatli yuborildi: {chat_id}")
    except Exception as e:
        logger.error(f"Golos yuborishda xato: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_ids.add(chat_id)

    logger.info(f"Start bosildi: {chat_id}")

    await update.message.reply_text(f"Assalomu alaykum {user.first_name}! 👋")
    await update.message.reply_text(f"🎬 Videoni YouTubeda tomosha qilishingiz mumkin:\n{VIDEO_LINK}")

    # 10 soniyadan keyin ovozli xabar yuborishni navbatga qo'yish
    context.job_queue.run_once(
        send_delayed_voice_msg,
        when=DELAY_SECONDS,
        data=chat_id,
        name=f"delayed_voice_{chat_id}",
    )

async def send_scheduled_voice(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Har kuni 09:00 da yuboriladigan ovozli xabar"""
    if not user_ids: return
    for chat_id in list(user_ids):
        try:
            if os.path.exists(DELAYED_VOICE):
                with open(DELAYED_VOICE, "rb") as f:
                    await context.bot.send_voice(chat_id=chat_id, voice=f, caption="🔊 Kunlik xabar!")
        except Exception as e:
            logger.error(f"Kunlik xabarda xato: {e}")

def main() -> None:
    request = HTTPXRequest(connect_timeout=20, read_timeout=60, write_timeout=60)
    application = Application.builder().token(BOT_TOKEN).request(request).build()

    application.add_handler(CommandHandler("start", start))

    # Kunlik vazifa (Har kuni 09:00)
    job_queue = application.job_queue
    scheduled_time = time(hour=SCHEDULED_HOUR, minute=SCHEDULED_MINUTE, tzinfo=TIMEZONE)
    job_queue.run_daily(send_scheduled_voice, time=scheduled_time)

    logger.info("Bot ishga tushdi...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()