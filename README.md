# Telegram Info Bot

A Telegram bot that provides technical information about groups and channels, primarily displaying chat IDs and metadata.

## Features

- Retrieves and displays group/channel IDs when the bot is added
- Shows basic group/channel metadata (member count, creation date if available)
- Displays chat type (group, supergroup, channel)
- Responds to specific commands for technical information
- Handles errors gracefully

## Commands

- `/start` - Introduction to the bot
- `/help` - Display available commands
- `/id` - Get the current chat ID
- `/info` - Display detailed information about this chat
- `/type` - Show the chat type (private, group, supergroup, channel)
- `/members` - Get the number of members (when available)

Additionally, you can @mention the bot in a message to get basic chat info.

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install aiogram python-dotenv
   