import logging
from datetime import datetime
from aiogram import types
from aiogram.dispatcher.filters import CommandHelp, CommandStart
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .utils import get_chat_info, format_chat_info, get_chat_admins, format_admin_info

logger = logging.getLogger(__name__)

class DatabaseMiddleware(BaseMiddleware):
    """Middleware to handle database operations"""
    
    def __init__(self, db, chat_model, app):
        """Initialize with the database and chat model"""
        self.db = db
        self.Chat = chat_model
        self.app = app  # Store Flask app for context
        self.update_queue = []  # Queue to store updates to process
        super(DatabaseMiddleware, self).__init__()
    
    async def on_pre_process_message(self, message: types.Message, data: dict):
        """Process message before handlers, update chat info in database"""
        # Skip service messages like edited_message, etc.
        if not message or not message.chat:
            return
        
        # Always mark new messages in group chats for processing
        try:
            chat_id = message.chat.id
            chat_type = message.chat.type
            
            # Use a simpler flag-based system not dependent on database
            # Set a flag on the message object directly
            if chat_type in ['group', 'supergroup']:
                message.is_in_group = True
                # Store basic info about the chat as first message
                await self._save_chat_info_safely(message.bot, message.chat)
            
        except Exception as e:
            logger.error(f"Error in message pre-processing: {e}")
        
    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        """Process callback query, update chat info in database"""
        if not callback_query.message or not callback_query.message.chat:
            return
        
        # No database interactions in middleware
    
    async def _save_chat_info_safely(self, bot, chat):
        """Queue chat info to be saved asynchronously"""
        try:
            # Create a task to update chat info in the database
            chat_id = chat.id
            chat_type = chat.type
            
            # This is just for logging activity - actual database updates 
            # will happen through explicit commands like /hello
            logger.info(f"Saw activity in chat ID: {chat_id}, type: {chat_type}")
            
        except Exception as e:
            logger.error(f"Error queuing chat info update: {e}")
            logger.exception("Full exception details:")

def register_handlers(dp, db_enabled=False):
    """
    Register message handlers for the bot.
    
    Args:
        dp: Aiogram dispatcher
        db_enabled: Whether database functionality is enabled
    """
    # Register global middleware for database support
    if db_enabled:
        from app import db, Chat, app
        # Store the db and Chat model for use in handlers
        dp.middleware.setup(DatabaseMiddleware(db, Chat, app))
    
    # Command handlers
    dp.register_message_handler(start_command, CommandStart())
    dp.register_message_handler(help_command, CommandHelp())
    dp.register_message_handler(id_command, commands=['id'])
    dp.register_message_handler(info_command, commands=['info'])
    dp.register_message_handler(type_command, commands=['type'])
    dp.register_message_handler(members_command, commands=['members'])
    dp.register_message_handler(hello_command, commands=['hello'])  # Added explicit hello command
    dp.register_message_handler(admins_command, commands=['admins'])  # Admin information command
    
    # New chat members handler
    dp.register_message_handler(new_chat_members, content_types=types.ContentTypes.NEW_CHAT_MEMBERS)
    
    # General message handler (will provide info when bot is @mentioned)
    dp.register_message_handler(message_handler, content_types=types.ContentTypes.TEXT)
    
    # Callback query handler for inline buttons
    dp.register_callback_query_handler(button_callback, lambda c: c.data.startswith('get_'))

async def start_command(message: types.Message):
    """Handler for /start command"""
    chat_type = message.chat.type
    
    # Different response based on chat type
    if chat_type == 'private':
        # In private chats, show introduction
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("📋 Get Chat ID", callback_data="get_id"),
            InlineKeyboardButton("ℹ️ Chat Info", callback_data="get_info"),
            InlineKeyboardButton("📊 Chat Type", callback_data="get_type"),
            InlineKeyboardButton("👥 Members", callback_data="get_members")
        )
        
        await message.reply(
            "👋 Hello! I'm a Telegram Info Bot.\n\n"
            "I can help you get technical information about chats. "
            "This is useful for setting up other bots.\n\n"
            "Add me to a group or channel and use /info to see details.\n"
            "Use /help to see all available commands.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        # In groups/channels, show group info
        try:
            logger.info(f"Start command received in chat: {message.chat.id}")
            chat_info = await get_chat_info(message.bot, message.chat.id)
            formatted_info = format_chat_info(chat_info)
            
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("📋 Get Chat ID", callback_data="get_id"),
                InlineKeyboardButton("📊 Chat Type", callback_data="get_type"),
                InlineKeyboardButton("👥 Members", callback_data="get_members"),
                InlineKeyboardButton("❓ Help", callback_data="show_help")
            )
            
            await message.reply(
                "👋 <b>Hello!</b> I'm a Telegram Info Bot.\n\n"
                "Here's the information about this chat:\n\n" + formatted_info,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error sending start command response in group: {e}")
            logger.exception("Full exception details:")
            
            # Fallback to simpler message
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("📋 Get Chat ID", callback_data="get_id"),
                InlineKeyboardButton("❓ Help", callback_data="show_help")
            )
            
            await message.reply(
                f"👋 <b>Hello!</b> I'm a Telegram Info Bot.\n\n"
                f"<b>Chat ID:</b> <code>{message.chat.id}</code>\n"
                f"<b>Chat Type:</b> {message.chat.type}\n\n"
                f"Use /info for more details or /help to see all commands.",
                parse_mode="HTML",
                reply_markup=keyboard
            )

async def help_command(message: types.Message):
    """Handler for /help command"""
    # Create inline keyboard with command buttons
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📋 Get Chat ID", callback_data="get_id"),
        InlineKeyboardButton("ℹ️ Chat Info", callback_data="get_info"),
        InlineKeyboardButton("📊 Chat Type", callback_data="get_type"),
        InlineKeyboardButton("👥 Members", callback_data="get_members"),
        InlineKeyboardButton("👮‍♂️ Admins", callback_data="get_admins")
    )
    
    help_text = (
        "🔍 <b>Available Commands</b>:\n\n"
        "/id - Get the current chat ID\n"
        "/info - Display detailed information about this chat\n"
        "/hello - Force the bot to respond with basic chat info\n"
        "/type - Show the chat type (private, group, supergroup, channel)\n"
        "/members - Get the number of members (when available)\n"
        "/admins - Get information about group administrators\n\n"
        "You can also @mention me in a message to get basic chat info.\n\n"
        "<i>Note: Some information may be limited based on my permissions and the chat type.</i>"
    )
    await message.reply(help_text, parse_mode="HTML", reply_markup=keyboard)

async def id_command(message: types.Message):
    """Handler for /id command"""
    chat_id = message.chat.id
    await message.reply(f"🆔 <b>Chat ID</b>: <code>{chat_id}</code>", parse_mode="HTML")

async def info_command(message: types.Message):
    """Handler for /info command"""
    try:
        chat_info = await get_chat_info(message.bot, message.chat.id)
        formatted_info = format_chat_info(chat_info)
        await message.reply(formatted_info, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error getting chat info: {e}")
        await message.reply(f"❌ Error getting chat information: {str(e)}")

async def type_command(message: types.Message):
    """Handler for /type command"""
    chat_type = message.chat.type
    type_description = {
        "private": "👤 This is a private chat with a user",
        "group": "👥 This is a basic group",
        "supergroup": "🔄 This is a supergroup (upgraded group with advanced features)",
        "channel": "📢 This is a channel (broadcast)"
    }.get(chat_type, f"Unknown chat type: {chat_type}")
    
    await message.reply(f"<b>Chat Type</b>: {chat_type}\n{type_description}", parse_mode="HTML")

async def members_command(message: types.Message):
    """Handler for /members command"""
    try:
        if message.chat.type in ["private"]:
            await message.reply("This command only works in groups and channels.")
            return
            
        chat = await message.bot.get_chat(message.chat.id)
        
        # Get member count for supergroups and channels
        if hasattr(chat, 'members_count') and chat.members_count is not None:
            await message.reply(f"👥 <b>Member count</b>: {chat.members_count}", parse_mode="HTML")
        else:
            await message.reply("Member count information is not available.")
    except Exception as e:
        logger.error(f"Error getting members count: {e}")
        await message.reply(f"❌ Error getting member count: {str(e)}")
        
async def admins_command(message: types.Message):
    """Handler for /admins command - display administrators information"""
    try:
        # Check if this is a group or channel
        if message.chat.type == "private":
            await message.reply("This command only works in groups and channels.")
            return
            
        # Let user know we're processing
        processing_msg = await message.reply("👮‍♂️ Getting administrators information...")
        
        # Get admins info
        chat_id = message.chat.id
        admins_info = await get_chat_admins(message.bot, chat_id)
        formatted_info = format_admin_info(admins_info)
        
        # Create inline keyboard with additional options
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("📋 Chat ID", callback_data="get_id"),
            InlineKeyboardButton("ℹ️ Chat Info", callback_data="get_info"),
            InlineKeyboardButton("❓ Help", callback_data="show_help")
        )
        
        # Send the formatted admin info
        await processing_msg.edit_text(
            formatted_info,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error getting admin information: {e}")
        logger.exception("Full exception details:")
        await message.reply(f"❌ Error getting administrator information: {str(e)}")

async def hello_command(message: types.Message):
    """Handler for /hello command - an explicit command to get bot to respond"""
    try:
        logger.info(f"Hello command received in chat: {message.chat.id}")
        chat_id = message.chat.id
        chat_type = message.chat.type
        
        # Create keyboard with info buttons
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("📋 Get Chat ID", callback_data="get_id"),
            InlineKeyboardButton("ℹ️ Chat Info", callback_data="get_info"),
            InlineKeyboardButton("📊 Chat Type", callback_data="get_type"),
            InlineKeyboardButton("❓ Help", callback_data="show_help")
        )
        
        # Start with immediate basic response
        await message.reply(
            f"👋 <b>Hello from tgDetailsBot!</b>\n\n"
            f"🆔 <b>Chat ID</b>: <code>{chat_id}</code>\n"
            f"📋 <b>Type</b>: {chat_type}\n\n"
            f"Click a button below or use /info for more details.",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        # Update database if needed
        try:
            from app import db, Chat
            # Check if this chat is already in database
            db_chat = db.session.query(Chat).filter_by(id=chat_id).first()
            
            if not db_chat:
                logger.info(f"New chat detected via hello command: {chat_id}")
                # Get full chat info
                chat_info = await get_chat_info(message.bot, chat_id)
                
                # Create new database entry
                new_chat = Chat(
                    id=chat_id,
                    title=chat_info.get('title'),
                    type=chat_type,
                    username=chat_info.get('username'),
                    first_name=chat_info.get('first_name'),
                    last_name=chat_info.get('last_name'),
                    members_count=chat_info.get('members_count')
                )
                db.session.add(new_chat)
                db.session.commit()
                logger.info(f"Added new chat to database: {chat_id}")
        except Exception as db_error:
            logger.error(f"Database error in hello command: {db_error}")
            # Continue even if database update fails
            
    except Exception as e:
        logger.error(f"Error in hello command: {e}")
        logger.exception("Full exception details:")
        
        # Simple fallback if anything fails
        await message.reply(
            f"👋 <b>Hello!</b>\n\n"
            f"<b>Chat ID</b>: <code>{message.chat.id}</code>\n\n"
            f"Use /info for details.",
            parse_mode="HTML"
        )

async def new_chat_members(message: types.Message):
    """Handler for new_chat_members event"""
    # Print all new members for debugging
    logger.info(f"new_chat_members event triggered in chat {message.chat.id}")
    logger.info(f"New members: {[u.id for u in message.new_chat_members]}")
    
    # Get bot's ID for comparison
    bot_info = await message.bot.get_me()
    bot_id = bot_info.id
    logger.info(f"Bot ID is: {bot_id}")
    
    # Check if our bot is among the new members
    bot_added = False
    for user in message.new_chat_members:
        logger.info(f"Checking user: {user.id} vs bot: {bot_id}")
        if user.id == bot_id:
            bot_added = True
            logger.info(f"Bot was added to chat: {message.chat.id} - {message.chat.title}")
            
            # Bot was added to a new chat, send info immediately
            try:
                # First, send an immediate welcome message
                initial_keyboard = InlineKeyboardMarkup(row_width=2)
                initial_keyboard.add(
                    InlineKeyboardButton("📋 Get Chat ID", callback_data="get_id"),
                    InlineKeyboardButton("❓ Help", callback_data="show_help")
                )
                
                welcome_message = await message.reply(
                    "👋 <b>Hello everyone!</b> I'm a bot that provides technical information about Telegram chats.\n\n"
                    "Getting chat details... please wait...",
                    parse_mode="HTML",
                    reply_markup=initial_keyboard
                )
                
                # Then get the detailed chat info
                chat_info = await get_chat_info(message.bot, message.chat.id)
                formatted_info = format_chat_info(chat_info)
                
                # Create detailed inline keyboard with command buttons
                detailed_keyboard = InlineKeyboardMarkup(row_width=2)
                detailed_keyboard.add(
                    InlineKeyboardButton("📋 Get Chat ID", callback_data="get_id"),
                    InlineKeyboardButton("📊 Chat Type", callback_data="get_type"),
                    InlineKeyboardButton("👥 Members", callback_data="get_members"),
                    InlineKeyboardButton("❓ Help", callback_data="show_help")
                )
                
                # Update the welcome message with detailed info
                await welcome_message.edit_text(
                    "👋 <b>Thanks for adding me!</b>\n\n"
                    "I can help you get technical information about this chat. "
                    "This is useful for setting up other bots.\n\n"
                    "<b>Chat Information:</b>\n\n" + formatted_info,
                    parse_mode="HTML",
                    reply_markup=detailed_keyboard
                )
                
                logger.info(f"Successfully sent welcome message to chat: {message.chat.id}")
                
            except Exception as e:
                logger.error(f"Error sending welcome info: {e}")
                logger.exception("Full exception details:")
                
                # If there was an error getting detailed info, send a simpler message
                try:
                    # Create simple keyboard with fewer options
                    simple_keyboard = InlineKeyboardMarkup(row_width=2)
                    simple_keyboard.add(
                        InlineKeyboardButton("📋 Get Chat ID", callback_data="get_id"),
                        InlineKeyboardButton("❓ Help", callback_data="show_help")
                    )
                    
                    await message.reply(
                        "👋 <b>Thanks for adding me!</b>\n\n"
                        f"<b>Chat ID:</b> <code>{message.chat.id}</code>\n"
                        f"<b>Chat Type:</b> {message.chat.type}\n\n"
                        "Use /info to see more details or /help for all commands.",
                        parse_mode="HTML",
                        reply_markup=simple_keyboard
                    )
                except Exception as inner_e:
                    logger.error(f"Failed to send fallback welcome message: {inner_e}")

async def message_handler(message: types.Message):
    """General message handler"""
    chat_id = message.chat.id
    chat_type = message.chat.type
    
    # Special handling for group chats
    if chat_type in ['group', 'supergroup'] and message.from_user:
        if message.from_user.is_bot:
            # Don't respond to other bots
            return
            
        # Check if this is the first message in a group chat (using simpler is_in_group flag)
        if getattr(message, 'is_in_group', False):
            logger.info(f"Group chat message detected: {chat_id}")
            # No automatic welcome now - better to use explicit commands
    
    # Check if the bot is mentioned in the message
    bot_info = await message.bot.get_me()
    bot_username = bot_info.username
    
    if message.text and f"@{bot_username}" in message.text:
        # Bot was mentioned, send basic info
        logger.info(f"Bot was mentioned in chat: {chat_id}")
        
        # Create inline keyboard with command buttons
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("ℹ️ More Info", callback_data="get_info"),
            InlineKeyboardButton("📊 Chat Type", callback_data="get_type"),
            InlineKeyboardButton("❓ Help", callback_data="show_help")
        )
        
        await message.reply(
            f"🤖 <b>Basic Chat Info</b>:\n"
            f"🆔 <b>Chat ID</b>: <code>{chat_id}</code>\n"
            f"📋 <b>Type</b>: {chat_type}\n\n"
            f"Use /hello or /info for more details.",
            parse_mode="HTML",
            reply_markup=keyboard
        )

async def button_callback(callback_query: types.CallbackQuery):
    """Handler for inline button callbacks"""
    chat_id = callback_query.message.chat.id
    action = callback_query.data
    
    try:
        if action == "get_id":
            # Create back button
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("« Back", callback_data="show_help"))
            
            await callback_query.message.edit_text(
                f"🆔 <b>Chat ID</b>: <code>{chat_id}</code>", 
                parse_mode="HTML",
                reply_markup=keyboard
            )
        
        elif action == "get_info":
            chat_info = await get_chat_info(callback_query.bot, chat_id)
            formatted_info = format_chat_info(chat_info)
            
            # Create back button
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("« Back", callback_data="show_help"))
            
            # If message is too long, send a new message instead of editing
            if len(formatted_info) > 4000:
                await callback_query.message.reply(
                    formatted_info, 
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                await callback_query.answer("Chat information sent in a new message")
            else:
                await callback_query.message.edit_text(
                    formatted_info, 
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
        
        elif action == "get_type":
            chat_type = callback_query.message.chat.type
            type_description = {
                "private": "👤 This is a private chat with a user",
                "group": "👥 This is a basic group",
                "supergroup": "🔄 This is a supergroup (upgraded group with advanced features)",
                "channel": "📢 This is a channel (broadcast)"
            }.get(chat_type, f"Unknown chat type: {chat_type}")
            
            # Create back button
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("« Back", callback_data="show_help"))
            
            await callback_query.message.edit_text(
                f"<b>Chat Type</b>: {chat_type}\n{type_description}", 
                parse_mode="HTML",
                reply_markup=keyboard
            )
        
        elif action == "get_members":
            if callback_query.message.chat.type in ["private"]:
                await callback_query.answer("This feature only works in groups and channels")
                return
                
            chat = await callback_query.bot.get_chat(chat_id)
            
            # Create back button
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("« Back", callback_data="show_help"))
            
            if hasattr(chat, 'members_count') and chat.members_count is not None:
                await callback_query.message.edit_text(
                    f"👥 <b>Member count</b>: {chat.members_count}", 
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            else:
                await callback_query.answer("Member count information is not available")
        
        elif action == "get_admins":
            try:
                if callback_query.message.chat.type in ["private"]:
                    await callback_query.answer("This feature only works in groups and channels")
                    return
                    
                # Create a temporary message to show we're loading
                await callback_query.answer("Getting admin information...")
                
                # Get admin information
                admins_info = await get_chat_admins(callback_query.bot, chat_id)
                formatted_info = format_admin_info(admins_info)
                
                # Create back button
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton("« Back", callback_data="show_help"))
                
                # If message is too long, send a new message instead of editing
                if len(formatted_info) > 4000:
                    await callback_query.message.reply(
                        formatted_info, 
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                    await callback_query.answer("Admin information sent in a new message")
                else:
                    await callback_query.message.edit_text(
                        formatted_info, 
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
            except Exception as e:
                logger.error(f"Error getting admin information via callback: {e}")
                logger.exception("Full exception details:")
                
                # Create back button
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton("« Back", callback_data="show_help"))
                
                await callback_query.message.edit_text(
                    f"❌ Error getting administrator information: {str(e)}",
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                
        elif action == "show_help":
            # Recreate the help keyboard
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("📋 Get Chat ID", callback_data="get_id"),
                InlineKeyboardButton("ℹ️ Chat Info", callback_data="get_info"),
                InlineKeyboardButton("📊 Chat Type", callback_data="get_type"),
                InlineKeyboardButton("👥 Members", callback_data="get_members"),
                InlineKeyboardButton("👮‍♂️ Admins", callback_data="get_admins")
            )
            
            help_text = (
                "🔍 <b>Available Commands</b>:\n\n"
                "/id - Get the current chat ID\n"
                "/info - Display detailed information about this chat\n"
                "/hello - Force the bot to respond with basic chat info\n"
                "/type - Show the chat type (private, group, supergroup, channel)\n"
                "/members - Get the number of members (when available)\n"
                "/admins - Get information about group administrators\n\n"
                "You can also @mention me in a message to get basic chat info.\n\n"
                "<i>Note: Some information may be limited based on my permissions and the chat type.</i>"
            )
            
            await callback_query.message.edit_text(
                help_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        
        # Answer the callback query to remove the loading indicator
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error handling button callback: {e}")
        await callback_query.answer(f"Error: {str(e)[:200]}")  # Limit error message length
