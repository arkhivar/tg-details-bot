# Overview

This is a **lightweight, stateless Telegram Info Bot** optimized for webhook deployment and fast cold starts. The bot provides technical information about groups, channels, and forum topics without any persistent storage dependencies. Built for cost-effective autoscale deployment with minimal resource footprint.

The application serves as a utility tool for Telegram administrators and developers who need quick access to technical chat information including chat IDs, forum topic detection, admin information, and forwarded message analysis without the complexity of database storage or long-running processes.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **FastAPI Webhook Server**: Lightweight web server handling Telegram webhook requests with minimal overhead
- **Aiogram Bot Framework**: Handles all Telegram bot interactions, message processing, and command handling  
- **Stateless Operation**: No database dependencies or persistent storage for maximum performance
- **Modular Handler System**: Bot handlers organized in separate modules optimized for webhook delivery

## Data Storage
- **Pure Stateless Design**: No persistent storage or database dependencies
- **Memory-Only Operation**: All processing handled in-memory for fastest response times
- **Zero Configuration**: No database setup or connection management required

## Bot Architecture
- **Command-Based Interface**: Supports commands like `/start`, `/help`, `/id`, `/info`, `/type`, `/members`, `/topics`, and `/admins`
- **Forum Topic Support**: Detects and displays topic IDs for forum supergroups with specialized handling
- **Mention Support**: Responds to @mentions with basic chat information
- **Error Handling**: Graceful error handling for unauthorized access and chat not found scenarios
- **Middleware System**: Database middleware for processing messages and updating chat information

## User Interface
- **Telegram Interface**: Interactive inline keyboards with dynamic button layouts
- **Forum Detection**: Automatic detection of forum supergroups with specialized topic buttons
- **Command-Based Interaction**: Comprehensive set of commands for accessing different information types
- **Structured Responses**: Clean, formatted output with appropriate emojis and code formatting

## Security and Configuration
- **Environment Variables**: Bot token and database URL configured via environment variables
- **Database Security**: Connection pooling with automatic reconnection and error handling
- **Logging System**: Comprehensive logging throughout the application for debugging and monitoring

# External Dependencies

## Core Frameworks
- **FastAPI**: Lightweight ASGI web framework for webhook endpoints
- **aiogram**: Telegram Bot API framework for Python in webhook mode
- **uvicorn**: ASGI server for production deployment

## Bot Features
- **Interactive Keyboards**: Dynamic inline button layouts that adapt to chat type
- **Forum Topic Detection**: Automatic recognition and ID extraction for forum supergroups
- **Admin Information**: Comprehensive administrator details with permission breakdown
- **Forwarded Message Analysis**: Enhanced format for analyzing forwarded content

## Environment and Utilities
- **python-dotenv**: Environment variable management
- **logging**: Built-in Python logging for application monitoring

## Required External Services
- **Telegram Bot API**: Requires a bot token from Telegram's BotFather
- **PostgreSQL Database**: Database service for persistent chat information storage
- **Environment Configuration**: Simple environment variable setup for deployment

## Configuration Requirements
- `TELEGRAM_BOT_TOKEN`: Bot token from Telegram BotFather
- Webhook URL: Set via set_webhook.py script after deployment