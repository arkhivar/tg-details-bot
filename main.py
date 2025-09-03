import logging
import os
from fastapi import FastAPI, Request
from aiogram import types
from dotenv import load_dotenv
from bot import create_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get bot token
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
    raise ValueError("TELEGRAM_BOT_TOKEN is required")

# Initialize bot
bot, dp = create_bot(BOT_TOKEN)

# Create FastAPI app
app = FastAPI(title="Telegram Info Bot", docs_url=None, redoc_url=None)

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "bot": "running"}

@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming webhook from Telegram"""
    try:
        # Get the update from request
        update_data = await request.json()
        update = types.Update(**update_data)
        
        # Process the update
        await dp.process_update(update)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
