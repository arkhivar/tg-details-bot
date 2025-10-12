import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from bot.handlers import router
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dp = Dispatcher()

# Include router
dp.include_router(router)

logger.info("Bot initialized for polling mode")

async def main():
    """Main function to run the bot"""
    # Delete webhook if any
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook deleted, starting polling...")

    # Start polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())