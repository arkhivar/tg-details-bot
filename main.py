import os
import asyncio
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, types

import bot as bot_pkg

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get bot token
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
    raise ValueError("TELEGRAM_BOT_TOKEN is required")

# Optional secret token for validating incoming webhook requests
# (must match the secret_token passed to setWebhook, see set_webhook.py)
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')

# Initialize bot and dispatcher (handlers are registered in bot/__init__.py)
bot, dp = bot_pkg.create_bot(BOT_TOKEN)

# ---------------------------------------------------------------------------
# Webhook mode: FastAPI ASGI app, served with gunicorn/uvicorn as `main:app`
# ---------------------------------------------------------------------------
app = FastAPI(title="tg-details-bot")

HEALTH_RESPONSE = {"status": "ok", "bot": "tg-details-bot", "mode": "webhook"}


@app.get("/")
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return HEALTH_RESPONSE


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Receive and process Telegram updates"""
    if WEBHOOK_SECRET:
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret != WEBHOOK_SECRET:
            logger.warning("Rejected webhook request with invalid secret token")
            raise HTTPException(status_code=403, detail="Forbidden")

    try:
        data = await request.json()
        update = types.Update(**data)
    except Exception as e:
        logger.error(f"Failed to parse webhook update: {e}")
        raise HTTPException(status_code=400, detail="Invalid update payload")

    # aiogram 2.x resolves `.bot` on objects from context; process_update
    # does not set it itself (the built-in webhook handler normally does)
    Bot.set_current(bot)
    await dp.process_update(update)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Polling mode: `python main.py`
# ---------------------------------------------------------------------------
async def main():
    """Main function to run the bot in polling mode"""
    # Delete webhook if any
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook deleted, starting polling...")

    # Start polling
    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())
