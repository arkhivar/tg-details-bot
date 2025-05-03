import logging
from aiogram import Bot, Dispatcher, executor
from .handlers import register_handlers

logger = logging.getLogger(__name__)

def start_bot(token):
    """
    Initialize and start the Telegram bot.
    
    Args:
        token (str): Telegram Bot API token
    """
    # Initialize bot and dispatcher
    bot = Bot(token=token)
    dp = Dispatcher(bot)
    
    # Register message handlers
    register_handlers(dp)
    
    # Start the bot
    logger.info("Bot is starting...")
    executor.start_polling(dp, skip_updates=True)
