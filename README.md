# tg-details-bot

A **stateless Telegram info bot** for retrieving technical information about groups, channels, and forum topics: chat ID extraction, forum topic detection, admin information, and forwarded message analysis — with no database and no persistent storage. Designed to be self-hosted on a VM.

## Features

- 🆔 **Chat ID Extraction**: Get technical IDs for groups, channels, and supergroups
- 📝 **Forum Topic Support**: Detect and extract topic IDs from forum supergroups
- 👮‍♂️ **Admin Information**: Comprehensive administrator details with permissions
- 📊 **Chat Analysis**: Type detection, member counts, and metadata
- 🔄 **Forwarded Message Analysis**: Enhanced format for analyzing forwarded content with special handling for privacy-protected forwards
- ⚡ **Stateless Design**: No database, minimal memory usage
- 📨 **Interactive Keyboards**: Dynamic inline buttons that adapt to chat type (forum detection)

## Requirements

- **Python 3.11** — NOTE: aiogram 2.25.1 has no prebuilt aiohttp wheels for Python 3.12+, so use Python 3.11
- A VM (any Linux box you control)
- A bot token from [@BotFather](https://t.me/BotFather)

## Quick start (polling)

```bash
git clone https://github.com/arkhivar/tg-details-bot.git
cd tg-details-bot
python3.11 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env   # edit: set TELEGRAM_BOT_TOKEN
venv/bin/python main.py
```

## Run as a service (systemd, polling)

A ready-made unit file is provided at `deploy/tg-details-bot.service`. It assumes the repo lives at `/opt/tg-details-bot` with a `venv/` inside it, and runs as user `tgbot` (create the user or adjust the unit).

```bash
sudo cp deploy/tg-details-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tg-details-bot
sudo systemctl start tg-details-bot
```

## Optional: webhook mode

For instant update delivery, serve the FastAPI app with gunicorn behind a TLS-terminating reverse proxy (nginx or caddy):

```bash
gunicorn -c gunicorn.conf.py main:app
```

Proxy `https://your-domain/webhook` to the gunicorn port (default `0.0.0.0:5000`), then register the webhook:

```bash
python set_webhook.py            # interactive: prompts for the public URL and sets the webhook
python set_webhook.py --status   # show current webhook info
python set_webhook.py --delete   # delete the webhook (return to polling)
```

Optionally set `WEBHOOK_SECRET` in `.env` — it is sent as `secret_token` to Telegram and validated on incoming requests via the `X-Telegram-Bot-Api-Secret-Token` header.

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

## File structure

```
├── bot/
│   ├── __init__.py        # Bot/dispatcher factory (create_bot) used by webhook mode
│   ├── handlers.py        # All command and message handlers
│   └── utils.py           # Helper functions for chat info, admin lists, formatting
├── deploy/
│   └── tg-details-bot.service  # systemd unit (polling mode)
├── main.py                # Entry point: FastAPI `app` (webhook) + `python main.py` (polling)
├── set_webhook.py         # Webhook configuration script (--delete / --status flags)
├── gunicorn.conf.py       # Gunicorn production server config (webhook mode)
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project metadata
└── .env.example           # Environment variable template
```

## Troubleshooting

### Bot Not Responding
1. Check that `TELEGRAM_BOT_TOKEN` is set correctly in `.env`
2. For webhook: verify the webhook with `python set_webhook.py --status`
3. For polling: ensure only one instance is running
4. Check logs: `journalctl -u tg-details-bot -f`

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

## License

Open source - feel free to fork and modify!
