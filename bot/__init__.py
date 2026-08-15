import logging
from aiogram import Bot, Dispatcher
from .handlers import register_handlers

logger = logging.getLogger(__name__)

def create_bot(token):
    """
    Initialize the Telegram bot.

    Args:
        token (str): Telegram Bot API token

    Returns:
        tuple: (bot, dispatcher) instances
    """
    # Initialize bot and dispatcher (aiogram 3.x: Dispatcher takes no bot)
    bot = Bot(token=token)
    dp = Dispatcher()

    # Register message handlers (no database needed)
    register_handlers(dp)

    logger.info("Bot initialized")
    return bot, dp
