import logging
import sys
import os
from aiogram import Bot, Dispatcher, executor
from .handlers import register_handlers

logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to allow importing database
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

# Import the database module
try:
    from database import db, Chat
    # Initialize database connection
    HAS_DB = db.connect()
    if HAS_DB:
        logger.info("Database connection established")
    else:
        logger.warning("Database connection failed. Chat tracking disabled.")
except ImportError as e:
    logger.warning(f"Could not import database models: {e}. Chat tracking disabled.")
    HAS_DB = False

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
