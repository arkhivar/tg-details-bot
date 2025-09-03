# Overview

This is a Telegram Info Bot project that provides technical information about groups and channels. The bot can retrieve and display chat IDs, metadata, member counts, forum topic IDs, and other technical information when added to groups or channels. 

The application serves as a utility tool for Telegram administrators and developers who need to quickly access technical information about chats, including chat IDs, types, member counts, administrative details, and forum topic support.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **Aiogram Bot Framework**: Handles all Telegram bot interactions, message processing, and command handling
- **Modular Handler System**: Bot handlers are organized in separate modules with middleware for database operations
- **Database Integration**: SQLAlchemy ORM with a Chat model to track bot interactions and chat metadata
- **Standalone Architecture**: Simplified bot-only design without web framework dependencies

## Data Storage
- **SQLAlchemy ORM**: Used for database abstraction with a declarative base model
- **Chat Tracking Model**: Stores chat information including ID, title, type, username, member count, and activity timestamps
- **Connection Pooling**: Configured with pool recycling and pre-ping for reliable database connections

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
- **aiogram**: Telegram Bot API framework for Python
- **SQLAlchemy**: ORM for database operations
- **psycopg2-binary**: PostgreSQL database adapter

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
- `DATABASE_URL`: PostgreSQL database connection string