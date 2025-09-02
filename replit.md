# Overview

This is a Telegram Info Bot project that provides technical information about groups and channels. The bot can retrieve and display chat IDs, metadata, member counts, and other technical information when added to groups or channels. The project includes both a Telegram bot backend and a web dashboard for monitoring bot interactions.

The application serves as a utility tool for Telegram administrators and developers who need to quickly access technical information about chats, including chat IDs, types, member counts, and administrative details.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **Flask Web Application**: Serves as the main web server with a dashboard interface for monitoring bot activity
- **Aiogram Bot Framework**: Handles all Telegram bot interactions, message processing, and command handling
- **Modular Handler System**: Bot handlers are organized in separate modules with middleware for database operations
- **Database Integration**: SQLAlchemy ORM with a Chat model to track bot interactions and chat metadata

## Data Storage
- **SQLAlchemy ORM**: Used for database abstraction with a declarative base model
- **Chat Tracking Model**: Stores chat information including ID, title, type, username, member count, and activity timestamps
- **Connection Pooling**: Configured with pool recycling and pre-ping for reliable database connections

## Bot Architecture
- **Command-Based Interface**: Supports commands like `/start`, `/help`, `/id`, `/info`, `/type`, and `/members`
- **Mention Support**: Responds to @mentions with basic chat information
- **Error Handling**: Graceful error handling for unauthorized access and chat not found scenarios
- **Middleware System**: Database middleware for processing messages and updating chat information

## Frontend Architecture
- **Bootstrap Dark Theme**: Uses Bootstrap with dark theme for the web dashboard
- **Real-time Statistics**: Dashboard displays chat statistics broken down by type (groups, supergroups, channels, private)
- **Responsive Design**: Mobile-friendly interface with card-based layout
- **Interactive Elements**: Search functionality and hover effects for better user experience

## Security and Configuration
- **Environment Variables**: Bot token and database URL configured via environment variables
- **Session Management**: Flask session handling with configurable secret key
- **Logging System**: Comprehensive logging throughout the application for debugging and monitoring

# External Dependencies

## Core Frameworks
- **aiogram**: Telegram Bot API framework for Python
- **Flask**: Web framework for the dashboard interface
- **SQLAlchemy**: ORM for database operations

## Frontend Libraries
- **Bootstrap**: CSS framework with dark theme variant
- **Custom CSS**: Additional styling for enhanced user experience

## Environment and Utilities
- **python-dotenv**: Environment variable management
- **logging**: Built-in Python logging for application monitoring

## Required External Services
- **Telegram Bot API**: Requires a bot token from Telegram's BotFather
- **Database Service**: Configured to work with any SQLAlchemy-compatible database
- **Web Hosting**: Designed to run on platforms that support Flask applications

## Configuration Requirements
- `TELEGRAM_BOT_TOKEN`: Bot token from Telegram BotFather
- `DATABASE_URL`: Database connection string
- `SESSION_SECRET`: Optional session secret for Flask (has default fallback)