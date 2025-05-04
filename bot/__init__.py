import logging
import sys
import os
from aiogram import Bot, Dispatcher, executor
from .handlers import register_handlers

logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to allow importing app
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

# Import the db and Chat model
try:
    from app import db, Chat, app
    HAS_DB = True
except ImportError:
    logger.warning("Could not import database models. Chat tracking disabled.")
    HAS_DB = False
    app = None

def start_bot(token):
    """
    Initialize and start the Telegram bot.
    
    Args:
        token (str): Telegram Bot API token
    """
    # Initialize bot and dispatcher
    bot = Bot(token=token)
    dp = Dispatcher(bot)
    
    # Register message handlers with the appropriate database connection
    register_handlers(dp, db_enabled=HAS_DB)
    
    # Start the bot
    logger.info("Bot is starting...")
    executor.start_polling(dp, skip_updates=True)
