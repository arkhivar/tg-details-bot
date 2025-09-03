#!/usr/bin/env python3
"""
Script to set up Telegram webhook for the bot
Run this after deploying to configure the webhook URL
"""
import os
import asyncio
import logging
from aiogram import Bot
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def set_webhook():
    load_dotenv()
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found!")
        return
    
    # This should be your deployed URL
    webhook_url = input("Enter your deployed webhook URL (e.g., https://your-app.replit.app/webhook): ")
    
    if not webhook_url.endswith('/webhook'):
        webhook_url += '/webhook'
    
    bot = Bot(token=bot_token)
    
    try:
        # Delete existing webhook first
        await bot.delete_webhook()
        logger.info("Deleted existing webhook")
        
        # Set new webhook
        await bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
        
        # Get webhook info to verify
        webhook_info = await bot.get_webhook_info()
        logger.info(f"Webhook info: {webhook_info}")
        
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(set_webhook())