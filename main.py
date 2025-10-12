
import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from bot.handlers import register_handlers
import logging

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

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Register handlers
register_handlers(dp)

logger.info("Bot initialized for polling mode")

async def main():
    """Main function to run the bot"""
    # Delete webhook if any
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook deleted, starting polling...")

    # Start polling
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())
