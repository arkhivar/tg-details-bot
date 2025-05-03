import logging
import os
from dotenv import load_dotenv

from bot import start_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    # Load environment variables
    load_dotenv()
    
    # Get bot token from environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        exit(1)
    
    # Start the bot
    logger.info("Starting Telegram Info Bot")
    start_bot(bot_token)
