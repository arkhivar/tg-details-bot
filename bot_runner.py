import logging
import os
from dotenv import load_dotenv

# Configure logging first
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import the app module - this is essential for the bot to access the database
try:
    from app import app, db, Chat
    logger.info("Successfully imported app modules")
    
    # Let's verify the database is properly configured
    if app.config["SQLALCHEMY_DATABASE_URI"]:
        logger.info(f"Database URL is configured: {app.config['SQLALCHEMY_DATABASE_URI'][:10]}...")
    else:
        logger.error("Database URL is not configured!")
        
except Exception as e:
    logger.error(f"Error importing app modules: {e}")
    logger.exception("Full exception details:")

# Import the bot module
from bot import start_bot

if __name__ == '__main__':
    # Load environment variables
    load_dotenv()
    
    # Get bot token from environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        exit(1)
    
    # Start the bot with detailed logging
    logger.info("Starting Telegram Info Bot")
    try:
        start_bot(bot_token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        logger.exception("Full exception details:")