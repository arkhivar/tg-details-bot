#!/usr/bin/env python3
"""
Script to set up Telegram webhook for the bot
Run this after deploying to configure the webhook URL

Usage:
    python set_webhook.py            # interactive: prompt for URL and set the webhook
    python set_webhook.py --delete   # delete the configured webhook
    python set_webhook.py --status   # show current webhook info

If the WEBHOOK_SECRET environment variable is set, it is passed as
secret_token to setWebhook (validated by main.py on incoming updates).
"""
import os
import asyncio
import argparse
import logging
from aiogram import Bot
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def set_webhook(bot):
    """Interactively prompt for the deployed URL and set the webhook"""
    # This should be your deployed URL
    webhook_url = input("Enter your deployed webhook URL (e.g., https://bot.example.com/webhook): ")

    if not webhook_url.endswith('/webhook'):
        webhook_url += '/webhook'

    # Delete existing webhook first
    await bot.delete_webhook()
    logger.info("Deleted existing webhook")

    # Set new webhook, passing secret_token if WEBHOOK_SECRET is configured
    webhook_secret = os.getenv('WEBHOOK_SECRET')
    if webhook_secret:
        await bot.set_webhook(url=webhook_url, secret_token=webhook_secret)
        logger.info("Webhook secret token enabled (WEBHOOK_SECRET)")
    else:
        await bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")

    # Get webhook info to verify
    webhook_info = await bot.get_webhook_info()
    logger.info(f"Webhook info: {webhook_info}")


async def delete_webhook(bot):
    """Delete the configured webhook"""
    await bot.delete_webhook()
    logger.info("Webhook deleted")


async def webhook_status(bot):
    """Show current webhook info"""
    webhook_info = await bot.get_webhook_info()
    logger.info(f"Webhook info: {webhook_info}")


async def main():
    load_dotenv()

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found!")
        return

    parser = argparse.ArgumentParser(description="Configure the Telegram webhook for this bot")
    parser.add_argument('--delete', action='store_true', help='Delete the configured webhook')
    parser.add_argument('--status', action='store_true', help='Show current webhook info')
    args = parser.parse_args()

    bot = Bot(token=bot_token)

    try:
        if args.delete:
            await delete_webhook(bot)
        elif args.status:
            await webhook_status(bot)
        else:
            await set_webhook(bot)
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
