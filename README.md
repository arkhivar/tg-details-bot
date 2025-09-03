# Lightweight Telegram Info Bot

This is a **pure stateless Telegram bot** designed for retrieving technical information about groups, channels, and forum topics. Built with a webhook-based architecture optimized for fast cold starts and cost-effective deployment on serverless platforms. The bot provides essential features like chat ID extraction, forum topic detection, admin information, and forwarded message analysis without any persistent storage overhead.

The bot eliminates all database dependencies and chat tracking to achieve **minimal resource footprint** and **blazing-fast startup times**. Using webhook delivery instead of polling ensures instant message processing while maintaining compatibility with autoscale deployments. Perfect for developers and Telegram administrators who need quick access to technical chat information without the complexity of persistent data storage or long-running processes.

## Features

- 🆔 **Chat ID Extraction**: Get technical IDs for groups, channels, and supergroups
- 📝 **Forum Topic Support**: Detect and extract topic IDs from forum supergroups  
- 👮‍♂️ **Admin Information**: Comprehensive administrator details with permissions
- 📊 **Chat Analysis**: Type detection, member counts, and metadata
- 🔄 **Forwarded Message Analysis**: Enhanced format for analyzing forwarded content
- ⚡ **Stateless Design**: No database, fast cold starts, minimal memory usage

## Deployment

### Replit Deployment (Recommended)

1. **Set Up Secrets**:
   - Add `TELEGRAM_BOT_TOKEN` to your Replit secrets

2. **Deploy with Autoscale**:
   - Create new Autoscale deployment 
   - Run command: `uvicorn main:app --host 0.0.0.0 --port 5000`
   - Wait for deployment URL

3. **Configure Webhook**:
   ```bash
   python set_webhook.py
   # Enter your deployment URL when prompted
   ```

### Manual Deployment

1. **Install Dependencies**:
   ```bash
   pip install fastapi uvicorn aiogram python-dotenv
   ```

2. **Set Environment Variables**:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ```

3. **Run the Server**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 5000
   ```

4. **Set Webhook**:
   ```bash
   python set_webhook.py
   ```

## Usage

Add the bot to any Telegram group, channel, or forum and use these commands:

- `/start` - Welcome message with quick actions
- `/id` - Get the current chat ID
- `/info` - Display detailed chat information  
- `/type` - Show chat type (group, supergroup, channel)
- `/members` - Get member count (when available)
- `/topics` - Show forum topic information (forum groups only)
- `/admins` - Get administrator information
- `/help` - Show all available commands

## Architecture

- **FastAPI**: Lightweight webhook server
- **Aiogram**: Telegram Bot API framework in webhook mode
- **Stateless**: No database, no persistent storage
- **Autoscale Ready**: Optimized for serverless deployment

## Cost Comparison

- **Traditional Polling Bot**: ~$10-20/month (Reserved VM required)
- **This Webhook Bot**: ~$3-4/month (Autoscale compatible)

## API Endpoints

- `GET /` - Health check
- `POST /webhook` - Telegram webhook receiver