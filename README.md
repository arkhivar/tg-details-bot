
# Lightweight Telegram Info Bot

This is a **pure stateless Telegram bot** designed for retrieving technical information about groups, channels, and forum topics. Built with a webhook-based architecture optimized for fast cold starts and cost-effective deployment on serverless platforms. The bot provides essential features like chat ID extraction, forum topic detection, admin information, and forwarded message analysis without any persistent storage overhead.

The bot eliminates all database dependencies and chat tracking to achieve **minimal resource footprint** and **blazing-fast startup times**. Using webhook delivery instead of polling ensures instant message processing while maintaining compatibility with autoscale deployments. Perfect for developers and Telegram administrators who need quick access to technical chat information without the complexity of persistent data storage or long-running processes.

## Features

- 🆔 **Chat ID Extraction**: Get technical IDs for groups, channels, and supergroups
- 📝 **Forum Topic Support**: Detect and extract topic IDs from forum supergroups  
- 👮‍♂️ **Admin Information**: Comprehensive administrator details with permissions
- 📊 **Chat Analysis**: Type detection, member counts, and metadata
- 🔄 **Forwarded Message Analysis**: Enhanced format for analyzing forwarded content with special handling for privacy-protected forwards
- ⚡ **Stateless Design**: No database, fast cold starts, minimal memory usage
- 📨 **Interactive Keyboards**: Dynamic inline buttons that adapt to chat type (forum detection)

## Architecture

### Tech Stack
- **FastAPI**: Lightweight ASGI web framework for webhook endpoints
- **Aiogram 2.25.1**: Telegram Bot API framework in webhook mode
- **Uvicorn/Gunicorn**: ASGI server for production deployment
- **Python 3.11+**: Modern Python with async/await support

### Key Design Decisions

1. **Stateless Operation**: No database means zero persistence overhead and instant cold starts
2. **Webhook-Based**: Uses POST /webhook endpoint instead of polling for real-time message delivery
3. **Autoscale Compatible**: Designed to work with serverless platforms that may shut down when idle
4. **Forum-Aware**: Special handling for Telegram's forum supergroups with topic ID detection

### File Structure

```
├── bot/
│   ├── __init__.py        # Bot/dispatcher factory (create_bot) used by webhook mode
│   ├── handlers.py        # All command and message handlers
│   └── utils.py           # Helper functions for chat info, admin lists, formatting
├── main.py                # Entry point: FastAPI `app` (webhook) + `python main.py` (polling)
├── set_webhook.py         # Webhook configuration script (--delete / --status flags)
├── run_gunicorn.py        # Helper to launch gunicorn with uvicorn workers
├── gunicorn.conf.py       # Gunicorn production server config
├── .replit                # Replit deployment configuration
└── pyproject.toml         # Python dependencies
```

## Setup Instructions

### Prerequisites
1. Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram
2. A Replit account (or any hosting platform that supports Python web apps)

### Replit Deployment (Recommended)

#### Step 1: Import to Replit
1. Fork this repository or import it as a new Repl
2. Replit will automatically detect it as a Python project

#### Step 2: Configure Environment
1. Open the Secrets tool (lock icon in left sidebar)
2. Add `TELEGRAM_BOT_TOKEN` with your bot token from BotFather
3. No other configuration needed - the bot is stateless!

#### Step 3: Choose Deployment Mode

**Option A: Webhook Mode (Recommended for Production)**
1. Create an Autoscale deployment
2. Set run command: `gunicorn --bind 0.0.0.0:5000 main:app`
3. Wait for deployment URL (e.g., `https://your-app.replit.app`)
4. Run `python set_webhook.py` and enter your deployment URL
5. Bot will respond instantly to messages via webhook

**Option B: Polling Mode (For Development/Testing)**
1. Click the Run button (already configured to run polling mode)
2. Bot runs continuously and polls Telegram for updates
3. Useful for testing but costs more on Replit

### Manual/Other Platform Deployment

```bash
# Install dependencies
pip install -r requirements.txt  # or use pyproject.toml

# Set environment variable
export TELEGRAM_BOT_TOKEN="your_bot_token_here"

# For webhook mode (production)
uvicorn main:app --host 0.0.0.0 --port 5000
# Then run: python set_webhook.py

# For polling mode (development)
python main.py
```

## Available Commands

### Basic Commands
- `/start` - Welcome message with interactive keyboard
- `/help` - Show all available commands
- `/id` - Get the current chat ID
- `/info` - Display detailed chat information
- `/type` - Show chat type (private, group, supergroup, channel)
- `/hello` - Force bot response with basic info

### Advanced Commands
- `/members` - Get member count (groups/channels only)
- `/topics` - Show forum topic information (forum supergroups only)
- `/admins` - Get administrator list with permissions breakdown
- `/forward_help` - Explain privacy limitations with forwarded messages

### Special Features
- **@mention support**: Mention the bot in any message to get chat info
- **Forward detection**: Forward any message to the bot to extract source chat/user ID
- **Interactive buttons**: Click buttons for quick access to different info types

## Important Notes

### Forwarded Message Handling
The bot has sophisticated logic for handling forwarded messages with Telegram's privacy restrictions:

1. **Public channels/groups**: Full chat ID extraction works
2. **Private groups**: Only works if bot is a member
3. **Privacy-protected forwards**: Shows user info but not source group ID
4. **Text mentions**: Detects both @usernames and text-mentioned users without usernames

See `/forward_help` command for detailed explanation of privacy limitations.

### Forum Support
- Automatically detects forum supergroups
- Extracts topic IDs from messages sent within specific topics
- Shows topic-aware button layout in forum chats
- Use `/topics` command to get current topic information

### Webhook vs Polling Trade-offs

**Webhook Mode:**
- ✅ Instant message delivery
- ✅ Lower cost (autoscale-friendly)
- ✅ Better for production
- ❌ Requires public URL
- ❌ More complex setup

**Polling Mode:**
- ✅ Easier to test locally
- ✅ No webhook setup needed
- ❌ Higher cost (always running)
- ❌ Slight delay in messages
- ❌ Not autoscale-compatible

## Cost Comparison

- **Polling on Replit**: ~$10-20/month (requires Reserved VM or Always-On)
- **Webhook on Autoscale**: ~$3-4/month (scales to zero when idle)

## Troubleshooting

### Bot Not Responding
1. Check that `TELEGRAM_BOT_TOKEN` is set correctly in Secrets
2. For webhook: Verify webhook is set with `python set_webhook.py`
3. For polling: Ensure only one instance is running
4. Check logs in the Console tab

### Webhook Issues
```bash
# Delete existing webhook
python set_webhook.py --delete

# Check webhook status
python set_webhook.py --status
```

### Permission Errors
- Bot needs to be added as administrator to get full admin list
- Member counts only available for supergroups/channels
- Some features require specific bot permissions

### Forum Detection Not Working
- Ensure the group is actually a forum (check in Telegram settings)
- Topic IDs only appear when commands are sent from within a topic
- General chat in forums won't have a topic ID

## Migration Checklist

When moving to a new Replit account:

1. ✅ Copy `TELEGRAM_BOT_TOKEN` to new Secrets
2. ✅ Import repository from GitHub or fork
3. ✅ Choose deployment mode (webhook recommended)
4. ✅ If webhook: Run `set_webhook.py` with new deployment URL
5. ✅ Test with `/start` command in Telegram
6. ✅ Verify inline buttons work
7. ✅ Test in a group to verify group features

## Development Notes

### Handler Registration Order Matters!
In `bot/handlers.py`, forward handlers are registered in specific order:
1. Direct channel forwards (best case)
2. Public group forwards with privacy settings
3. Fallback for any remaining forwards

This ensures the most specific handler catches each forward type first.

### Inline Keyboard Logic
Buttons change based on chat type:
- Private chats: Show all info buttons
- Groups: Show group-relevant buttons
- Forums: Add "Topics" button automatically

See `button_callback()` and `show_help` action in handlers.py.

### Forum Topic Detection
Uses `message.message_thread_id` to detect current topic. This is only available when:
- Chat is a forum supergroup (`is_forum=True`)
- Message is sent within a specific topic (not general chat)

## API Reference

### Main Endpoints (Webhook Mode)
- `GET /` and `GET /health` - Health checks
- `POST /webhook` - Telegram webhook receiver (validates `X-Telegram-Bot-Api-Secret-Token` header if `WEBHOOK_SECRET` is set)

### Key Functions in `bot/utils.py`
- `get_chat_info(bot, chat_id)` - Retrieves comprehensive chat details
- `format_chat_info(info)` - Formats chat info into readable HTML
- `get_chat_admins(bot, chat_id)` - Gets admin list with permissions
- `format_admin_info(info)` - Formats admin list into readable HTML
- `detect_topic_from_message(message)` - Extracts topic ID from message

## Contributing

This bot is designed to be stateless and simple. When adding features:
- Avoid adding database dependencies
- Keep cold start time fast
- Maintain webhook compatibility
- Update this README with any architectural changes

## License

Open source - feel free to fork and modify!

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review handler logic in `bot/handlers.py`
3. Check logs in Replit Console
4. Verify Telegram API limits haven't been hit

---

**Last Updated**: 2024 - Stateless webhook architecture for cost-effective Telegram bot hosting
