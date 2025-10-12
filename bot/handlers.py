import logging
from aiogram import types
from aiogram.dispatcher.filters import CommandHelp, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .utils import get_chat_info, format_chat_info, get_chat_admins, format_admin_info

logger = logging.getLogger(__name__)

def register_handlers(dp):
    """
    Register message handlers for the bot.

    Args:
        dp: Aiogram dispatcher
    """

    # Command handlers
    dp.register_message_handler(start_command, CommandStart())
    dp.register_message_handler(help_command, CommandHelp())
    dp.register_message_handler(id_command, commands=['id'])
    dp.register_message_handler(info_command, commands=['info'])
    dp.register_message_handler(type_command, commands=['type'])
    dp.register_message_handler(members_command, commands=['members'])
    dp.register_message_handler(topics_command, commands=['topics'])  # Forum topics command
    dp.register_message_handler(hello_command, commands=['hello'])  # Added explicit hello command
    dp.register_message_handler(admins_command, commands=['admins'])  # Admin information command
    dp.register_message_handler(forward_help_command, commands=['forward_help'])  # Special command to explain forward limitations

    # New chat members handler
    dp.register_message_handler(new_chat_members, content_types=types.ContentTypes.NEW_CHAT_MEMBERS)

    # Register specialized forward handlers first - order matters!

    # First: Handler for direct channel forwards where we can get the chat ID directly
    dp.register_message_handler(
        simple_forward_handler,
        lambda message: (
            hasattr(message, 'forward_date') and message.forward_date is not None and
            (message.forward_from_chat is not None or
             (hasattr(message, 'forward_origin') and 
              hasattr(message.forward_origin, 'chat') and 
              message.forward_origin.chat is not None))
        ),
        content_types=types.ContentTypes.ANY
    )

    # Second: Handler for public group forwards that need special explanation
    dp.register_message_handler(
        public_group_forward_handler,
        lambda message: (
            hasattr(message, 'forward_date') and message.forward_date is not None and 
            (
                # Direct check for group origins
                (hasattr(message, 'forward_origin') and 
                 getattr(message.forward_origin, 'type', '') in ['channel', 'chat', 'group']) or

                # Public group with privacy settings (user origin but text suggests it's from a group)
                (hasattr(message, 'caption') and message.caption and '@' in message.caption) or
                (hasattr(message, 'text') and message.text and '@' in message.text) or

                # Message has entities that suggest it's from a group but not accessible
                (hasattr(message, 'caption_entities') and message.caption_entities) or
                (hasattr(message, 'entities') and message.entities and 
                 any(e.type == 'mention' for e in message.entities)) or

                # Message is forwarded from user but has group context clues
                (hasattr(message, 'forward_from') and message.forward_from and 
                 hasattr(message, 'text') and message.text and 
                 ('<' in message.text or '>' in message.text))
            )
        ),
        content_types=types.ContentTypes.ANY
    )

    # Last: Fallback handler for any remaining forwards
    dp.register_message_handler(
        simple_forward_handler, 
        lambda message: hasattr(message, 'forward_date') and message.forward_date is not None,
        content_types=types.ContentTypes.ANY
    )

    # General message handler (will provide info when bot is @mentioned)
    dp.register_message_handler(message_handler, content_types=types.ContentTypes.TEXT)

    # Callback query handler for inline buttons
    dp.register_callback_query_handler(button_callback, lambda c: c.data.startswith('get_') or c.data == 'group_id_help')

async def start_command(message: types.Message):
    """Handler for /start command"""
    chat_type = message.chat.type

    # Different response based on chat type
    if chat_type == 'private':
        # In private chats, show introduction
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
            InlineKeyboardButton(text="ℹ️ Chat Info", callback_data="get_info"),
            InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
            InlineKeyboardButton(text="👥 Members", callback_data="get_members")
        )

        await message.reply(
            "👋 Hello! I'm a Telegram Info Bot.\n\n"
            "I can help you get technical information about chats. "
            "This is useful for setting up other bots.\n\n"
            "Add me to a group or channel and use /info to see details.\n"
            "Forward any message from a group/channel to me to get its chat ID.\n"
            "Forward a message with @username or text mentions to see detected users and their IDs.\n"
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
                InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
                InlineKeyboardButton(text="👥 Members", callback_data="get_members"),
                InlineKeyboardButton(text="❓ Help", callback_data="show_help")
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
                InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                InlineKeyboardButton(text="❓ Help", callback_data="show_help")
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
        InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
        InlineKeyboardButton(text="ℹ️ Chat Info", callback_data="get_info"),
        InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
        InlineKeyboardButton(text="👥 Members", callback_data="get_members"),
        InlineKeyboardButton(text="👮‍♂️ Admins", callback_data="get_admins"),
        InlineKeyboardButton(text="❓ Group ID Help", callback_data="group_id_help")
    )

    help_text = (
        "🔍 <b>Available Commands</b>:\n\n"
        "/id - Get the current chat ID\n"
        "/info - Display detailed information about this chat\n"
        "/hello - Force the bot to respond with basic chat info\n"
        "/type - Show the chat type (private, group, supergroup, channel)\n"
        "/members - Get the number of members (when available)\n"
        "/admins - Get information about group administrators\n"
        "/forward_help - Explain why group IDs from forwards sometimes don't work\n\n"
        "📨 <b>Get Group/Channel IDs</b>:\n"
        "<b>Method 1 (Recommended)</b>: Add me to the group/channel and use /id command.\n"
        "<b>Method 2</b>: Forward a message from a public group/channel, and I'll show the source chat ID.\n\n"
        "⚠️ <b>Important Limitation</b>: Due to Telegram's privacy restrictions, I can only get group IDs from forwarded messages if:\n"
        "- The source is a public group/channel, OR\n"
        "- I'm already a member of that group/channel\n\n"
        "You can also @mention me in a message to get basic chat info.\n\n"
        "👤 <b>User Detection</b>: I can detect both @usernames and users without usernames in forwarded messages.\n\n"
        "❓ <b>Trouble getting group IDs?</b> Use /forward_help for a detailed explanation.\n\n"
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

        # Add forum topic detection if this is a forum
        if chat_info.get('is_forum'):
            from bot.utils import detect_topic_from_message
            topic_info = detect_topic_from_message(message)

            if topic_info.get('topic_id'):
                formatted_info += f"\n\n🎯 <b>Current Topic ID</b>: {topic_info['topic_id']}"
                formatted_info += f"\n\n💡 <b>Tip</b>: Use /info for detailed information or /topics for forum-specific details"
            else:
                formatted_info += f"\n\n💡 <b>Tip</b>: Use /topics for forum-specific details"

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

async def topics_command(message: types.Message):
    """Handler for /topics command - shows forum topic information"""
    try:
        if message.chat.type in ["private"]:
            await message.reply("This command only works in groups and channels.")
            return

        # Check if this is a forum
        if hasattr(message.chat, 'is_forum') and message.chat.is_forum:
            # Get topic information from current message
            from bot.utils import detect_topic_from_message
            topic_info = detect_topic_from_message(message)

            response = f"📝 <b>Forum Topics Information</b>\n\n"
            response += f"🆔 <b>Chat ID</b>: <code>{message.chat.id}</code>\n"
            response += f"📊 <b>Is Forum</b>: Yes\n"
            response += f"📢 <b>Title</b>: {message.chat.title}\n\n"

            if topic_info.get('topic_id'):
                response += f"🎯 <b>Current Topic ID</b>: <code>{topic_info['topic_id']}</code>\n"
                response += f"📍 <b>You are currently in topic ID {topic_info['topic_id']}</b>\n\n"
            else:
                response += f"📍 <b>General Topic</b> (no specific topic ID)\n\n"

            response += f"💡 <b>Note</b>: This bot can detect the current topic ID when you send commands from within a specific topic. "
            response += f"To get topic IDs from other topics, send this command from those topics.\n\n"
            response += f"🔧 <b>For Developers</b>: Use the topic ID as the message_thread_id when sending messages to specific topics via the Bot API."

            # Create keyboard
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton(text="📋 Chat ID", callback_data="get_id"),
                InlineKeyboardButton(text="ℹ️ More Info", callback_data="get_info"),
                InlineKeyboardButton(text="❓ Help", callback_data="show_help")
            )

            await message.reply(response, parse_mode="HTML", reply_markup=keyboard)
        else:
            await message.reply(
                "📝 <b>Forum Topics</b>\n\n"
                "This chat is not a forum supergroup. Forum topics are only available in forum-enabled supergroups.\n\n"
                "To use forum features:\n"
                "1. Create or convert a supergroup to a forum\n" 
                "2. Enable 'Topics' in the group settings\n"
                "3. Add this bot to the forum group",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Error in topics command: {e}")
        await message.reply(f"❌ Error getting topic information: {str(e)}")

async def forward_help_command(message: types.Message):
    """Dedicated command to explain why group IDs might not be available in forwards"""
    explanation = (
        "<b>📚 Why Can't I Get Group IDs from Forwards?</b>\n\n"
        "This is a common issue with Telegram's privacy design:\n\n"
        "<b>Technical Explanation:</b>\n"
        "• When forwarding from public groups, Telegram intentionally hides the original group ID\n"
        "• The forward appears to come from the original sender (user) instead of the group\n"
        "• This is a privacy feature by design, not a limitation of this bot\n"
        "• Even in forwards from public groups, Telegram only shows user information\n\n"

        "<b>Why This Happens:</b>\n"
        "Telegram does this to prevent tracking and data collection across groups. Only bot developers "
        "who add their bots to groups can access group IDs directly.\n\n"

        "<b>Solutions:</b>\n"
        "1️⃣ <b>Add this bot directly to the group</b> (recommended)\n"
        "2️⃣ For public groups, use @username instead of ID in API calls\n"
        "3️⃣ For user accounts (not bots), open forwarded message in Telegram apps and look for the source group link\n"
        "4️⃣ For private groups, add this bot as member\n\n"

        "<b>In your screenshot:</b>\n"
        "The message was detected as a user forward because Telegram provides the user info, not the group info, "
        "even though it originated in a group.\n\n"

        "If you need more technical explanations, feel free to ask!"
    )

    await message.reply(explanation, parse_mode="HTML")

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

        # Create back button - always use show_help which handles forum detection
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text="« Back", callback_data="show_help"))

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
            InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
            InlineKeyboardButton(text="ℹ️ Chat Info", callback_data="get_info"),
            InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
            InlineKeyboardButton(text="❓ Help", callback_data="show_help")
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

        # Log chat interaction for stateless operation
        logger.info(f"Hello command used in chat: {chat_id} ({chat_type})")

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
                    InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                    InlineKeyboardButton(text="❓ Help", callback_data="show_help")
                )

                welcome_message = await message.reply(
                    "👋 <b>Hello everyone!</b> I'm a bot that provides technical information about Telegram chats.\n\n"
                    "Getting chat details... please wait...",
                    parse_mode="HTML",
                    reply_markup=initial_keyboard
                )

                # Then get the detailed chat info
                chat_info = await get_chat_info(message.bot, message.chat.id)

                # Check if this is a forum and add topic information
                topic_info_text = ""
                if chat_info.get('is_forum'):
                    from bot.utils import detect_topic_from_message
                    topic_info = detect_topic_from_message(message)
                    if topic_info.get('topic_id'):
                        topic_info_text = f"\n🎯 <b>Current Topic ID</b>: <code>{topic_info['topic_id']}</code>\n💡 <b>Use /topics command to get more topic information</b>\n"
                    else:
                        topic_info_text = f"\n📝 <b>Forum detected!</b> Use /topics command for topic information\n"

                formatted_info = format_chat_info(chat_info) + topic_info_text

                # Create detailed inline keyboard with command buttons
                detailed_keyboard = InlineKeyboardMarkup(row_width=2)
                # Add different buttons based on whether it's a forum
                if chat_info.get('is_forum'):
                    detailed_keyboard.add(
                        InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                        InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
                        InlineKeyboardButton(text="👥 Members", callback_data="get_members"),
                        InlineKeyboardButton(text="📝 Topics", callback_data="get_topics"),
                        InlineKeyboardButton(text="❓ Help", callback_data="show_help")
                    )
                else:
                    detailed_keyboard.add(
                        InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                        InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
                        InlineKeyboardButton(text="👥 Members", callback_data="get_members"),
                        InlineKeyboardButton(text="❓ Help", callback_data="show_help")
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
                        InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                        InlineKeyboardButton(text="❓ Help", callback_data="show_help")
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

async def public_group_forward_handler(message: types.Message):
    """Handler specifically for public group forwards that need special explanation"""
    logger.info(f"=== PUBLIC GROUP FORWARD DETECTED ===")
    if hasattr(message, 'to_python'):
        logger.info(f"Message data: {message.to_python()}")

    # Extract as much information as possible from the forwarded message
    has_forward_origin = hasattr(message, 'forward_origin')
    has_forward_from = message.forward_from is not None
    has_forward_from_chat = message.forward_from_chat is not None
    has_forward_sender_name = hasattr(message, 'forward_sender_name') and message.forward_sender_name

    logger.info(f"Forward detection: origin={has_forward_origin}, from={has_forward_from}, from_chat={has_forward_from_chat}, sender_name={has_forward_sender_name}")

    # Create keyboard with help button
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text="❓ Why can't I get the group ID?", callback_data="group_id_help")
    )

    # First try to get direct chat information if available
    if has_forward_from_chat:
        # This is the best case - we have direct chat info
        chat = message.forward_from_chat
        forward_info = (
            f"📨 <b>Forwarded Message Info</b>\n\n"
            f"✅ <b>SUCCESS</b>: Chat information found!\n\n"
            f"🆔 <b>Chat ID</b>: <code>{chat.id}</code>\n"
            f"📋 <b>Chat Type</b>: {chat.type}\n"
        )

        if getattr(chat, 'title', None):
            forward_info += f"📢 <b>Title</b>: {chat.title}\n"

        if getattr(chat, 'username', None):
            forward_info += f"👤 <b>Username</b>: @{chat.username}\n"
            forward_info += f"🔗 <b>Link</b>: https://t.me/{chat.username}\n"

        await message.reply(forward_info, parse_mode="HTML")
        return

    # Second, try to extract from forward_origin
    if has_forward_origin:
        origin_type = getattr(message.forward_origin, 'type', 'unknown')
        logger.info(f"Forward origin type: {origin_type}")

        # Check if we have sender_chat in origin
        if hasattr(message.forward_origin, 'sender_chat') and message.forward_origin.sender_chat:
            chat = message.forward_origin.sender_chat
            forward_info = (
                f"📨 <b>Forwarded Message Info</b>\n\n"
                f"✅ <b>SUCCESS</b>: Chat information found!\n\n"
                f"🆔 <b>Chat ID</b>: <code>{chat.id}</code>\n"
                f"📋 <b>Chat Type</b>: {getattr(chat, 'type', 'unknown')}\n"
            )

            if getattr(chat, 'title', None):
                forward_info += f"📢 <b>Title</b>: {chat.title}\n"

            if getattr(chat, 'username', None):
                forward_info += f"👤 <b>Username</b>: @{chat.username}\n"
                forward_info += f"🔗 <b>Link</b>: https://t.me/{chat.username}\n"

            await message.reply(forward_info, parse_mode="HTML")
            return

        # Check if we have direct chat attribute
        if hasattr(message.forward_origin, 'chat') and message.forward_origin.chat:
            chat = message.forward_origin.chat
            forward_info = (
                f"📨 <b>Forwarded Message Info</b>\n\n"
                f"✅ <b>SUCCESS</b>: Chat information found!\n\n"
                f"🆔 <b>Chat ID</b>: <code>{chat.id}</code>\n"
                f"📋 <b>Chat Type</b>: {getattr(chat, 'type', 'unknown')}\n"
            )

            if getattr(chat, 'title', None):
                forward_info += f"📢 <b>Title</b>: {chat.title}\n"

            if getattr(chat, 'username', None):
                forward_info += f"👤 <b>Username</b>: @{chat.username}\n"
                forward_info += f"🔗 <b>Link</b>: https://t.me/{chat.username}\n"

            await message.reply(forward_info, parse_mode="HTML")
            return

    # If we got here, we couldn't get the group ID - create detailed explanation
    forward_info = (
        f"📨 <b>Forwarded Message Info</b>\n\n"
        f"❌ <b>UNABLE TO GET GROUP ID</b>\n\n"
        f"ℹ️ Due to Telegram's API limitations, this bot cannot extract the original group ID from this forwarded message.\n\n"
        f"This typically happens with public groups where the bot is not a member.\n\n"
        f"💡 <b>Solutions:</b>\n"
        f"1. Add this bot to the group directly\n"
        f"2. Forward a message from a channel or a private group\n"
        f"3. If you're an admin, temporarily toggle the group to private, forward a message, then set it back\n\n"
        f"If the group has an @username, you can access it via the API with that username instead of an ID."
    )

    # Try to extract any identifiable information
    if hasattr(message, 'forward_origin') and message.forward_origin:
        # Get any user information if available
        if hasattr(message.forward_origin, 'sender_user') and message.forward_origin.sender_user:
            user = message.forward_origin.sender_user
            forward_info += f"\n👤 <b>User ID</b>: <code>{user.id}</code>\n"

            if getattr(user, 'username', None):
                forward_info += f"👤 <b>Username</b>: @{user.username}\n"
                forward_info += f"🔗 <b>Link</b>: https://t.me/{user.username}\n"

            name_parts = []
            if getattr(user, 'first_name', None):
                name_parts.append(user.first_name)
            if getattr(user, 'last_name', None):
                name_parts.append(user.last_name)

            if name_parts:
                forward_info += f"👤 <b>Name</b>: {' '.join(name_parts)}\n\n"
                forward_info += f"⚠️ <i>This is the user's ID, not the group ID. See 'Why can't I get the group ID' button below.</i>"
        origin_type = getattr(message.forward_origin, 'type', 'unknown')
        forward_info += f"\n\n<b>Origin Type</b>: {origin_type}"

        # Try to extract any identifiable information from entities
        # Check for mentions in the text (might help identify the source)
        mentioned_entities = []
        text_mentioned_users = []

        if hasattr(message, 'entities') and message.entities and hasattr(message, 'text') and message.text:
            for entity in message.entities:
                if entity.type == 'mention':
                    mention_text = message.text[entity.offset:entity.offset + entity.length]
                    mentioned_entities.append(mention_text)
                elif entity.type == 'text_mention' and hasattr(entity, 'user'):
                    user = entity.user
                    user_text = message.text[entity.offset:entity.offset + entity.length]
                    user_info = f"{user_text} (ID: {user.id})"
                    text_mentioned_users.append(user_info)

            # Add mentions to the message if we found any
            if mentioned_entities:
                forward_info += f"\n\n📢 <b>Mentioned</b>: {', '.join(mentioned_entities)}\n"
                forward_info += f"⚠️ <i>This might be the group the message is from, but we can't confirm.</i>"

            if text_mentioned_users:
                forward_info += f"\n\n👤 <b>Text Mentioned Users</b>: {', '.join(text_mentioned_users)}\n"

    # Add the help button to get the detailed explanation
    await message.reply(forward_info, parse_mode="HTML", reply_markup=keyboard)

async def simple_forward_handler(message: types.Message):
    """Simple, reliable handler for all types of forwarded messages"""
    # Log what we got for debugging
    logger.info(f"=== FORWARD DEBUG INFO ===")
    logger.info(f"Message ID: {message.message_id}")
    logger.info(f"From User: {message.from_user.id} - {getattr(message.from_user, 'username', 'No username')}")

    # Track what kind of forward this is
    has_from_chat = message.forward_from_chat is not None
    has_from_user = message.forward_from is not None
    has_sender_name = getattr(message, 'forward_sender_name', None) is not None
    has_origin = hasattr(message, 'forward_origin')

    # Log the forward type
    logger.info(f"Forward type: from_chat={has_from_chat}, from_user={has_from_user}, sender_name={has_sender_name}, has_origin={has_origin}")

    # Start building the response message with the new format
    source_info = ""  # For the source group/channel
    user_info = ""    # For the user information
    success_msg = ""  # For the success message
    success = False

    # Keyboard for when we need help button
    help_keyboard = InlineKeyboardMarkup(row_width=1)
    help_keyboard.add(
        InlineKeyboardButton(text="❓ Why can't I get the group ID?", callback_data="group_id_help")
    )

    # SECTION 1: SOURCE GROUP/CHANNEL INFO

    # Case 1: We have forward_from_chat - this is the most reliable case
    if has_from_chat:
        chat = message.forward_from_chat
        chat_type = chat.type.upper()
        source_info = f"SOURCE {chat_type}: ID <code>{chat.id}</code>\n"

        if getattr(chat, 'title', None):
            source_info += f"📢 Title: {chat.title}\n"

        if getattr(chat, 'username', None):
            source_info += f"👤 Username: @{chat.username}\n"
            source_info += f"🔗 Link: https://t.me/{chat.username}\n"

        # Add original message ID and link if available
        if getattr(message, 'forward_from_message_id', None):
            source_info += f"🔢 Message ID: {message.forward_from_message_id}\n"

            if getattr(chat, 'username', None):
                source_info += f"🔗 Message Link: https://t.me/{chat.username}/{message.forward_from_message_id}\n"

        success = True

    # Try origin.chat
    elif has_origin and hasattr(message.forward_origin, 'chat') and message.forward_origin.chat:
        chat = message.forward_origin.chat
        chat_type = getattr(chat, 'type', 'GROUP').upper()
        source_info = f"SOURCE {chat_type}: ID <code>{chat.id}</code>\n"

        if getattr(chat, 'title', None):
            source_info += f"📢 Title: {chat.title}\n"

        if getattr(chat, 'username', None):
            source_info += f"👤 Username: @{chat.username}\n"
            source_info += f"🔗 Link: https://t.me/{chat.username}\n"

        success = True

    # Try origin.sender_chat
    elif has_origin and hasattr(message.forward_origin, 'sender_chat') and message.forward_origin.sender_chat:
        chat = message.forward_origin.sender_chat
        chat_type = getattr(chat, 'type', 'GROUP').upper()
        source_info = f"SOURCE {chat_type}: ID <code>{chat.id}</code>\n"

        if getattr(chat, 'title', None):
            source_info += f"📢 Title: {chat.title}\n"

        if getattr(chat, 'username', None):
            source_info += f"👤 Username: @{chat.username}\n"
            source_info += f"🔗 Link: https://t.me/{chat.username}\n"

        success = True

    # No source group info available
    else:
        source_info = "SOURCE GROUP: unavailable\n"
        if has_origin:
            origin_type = getattr(message.forward_origin, 'type', 'unknown')
            if origin_type not in ['user', 'unknown']:
                source_info += f"Origin type: {origin_type}\n"
            source_info += "⚠️ Unable to retrieve group ID due to privacy settings\n"

    # SECTION 2: USER INFO

    # Case for direct user forward
    if has_from_user:
        user = message.forward_from
        user_info = f"Forwarded from User 🆔 <code>{user.id}</code>\n"

        if getattr(user, 'username', None):
            user_info += f"👤 Username: @{user.username}\n"
            user_info += f"🔗 Link: https://t.me/{user.username}\n"

        # Add name information 
        name_parts = []
        if getattr(user, 'first_name', None):
            name_parts.append(user.first_name)
        if getattr(user, 'last_name', None):
            name_parts.append(user.last_name)

        if name_parts:
            user_info += f"👤 Name: {' '.join(name_parts)}\n"

        # If we only have user info but no source, set success for user
        if not success:
            success = True

    # Case for user info from forward_origin
    elif has_origin and hasattr(message.forward_origin, 'sender_user') and message.forward_origin.sender_user:
        user = message.forward_origin.sender_user
        user_info = f"Forwarded from User 🆔 <code>{user.id}</code>\n"

        if getattr(user, 'username', None):
            user_info += f"👤 Username: @{user.username}\n"
            user_info += f"🔗 Link: https://t.me/{user.username}\n"

        # Add name information
        name_parts = []
        if getattr(user, 'first_name', None):
            name_parts.append(user.first_name)
        if getattr(user, 'last_name', None):
            name_parts.append(user.last_name)

        if name_parts:
            user_info += f"👤 Name: {' '.join(name_parts)}\n"

        # If we only have user info but no source, set success for user
        if not success:
            success = True

    # Case for hidden user (only name)
    elif has_sender_name:
        user_info = f"Forwarded from User: {message.forward_sender_name}\n"
        user_info += "⚠️ User ID not available due to privacy settings\n"

    # SECTION 3: SUCCESS MESSAGE
    if success:
        if has_from_user or (has_origin and hasattr(message.forward_origin, 'sender_user')):
            success_msg = "✅ SUCCESS: The user ID was successfully retrieved!"
        else:
            # For chat/channel/group
            chat_type = "chat"
            if has_from_chat:
                chat_type = message.forward_from_chat.type
            elif has_origin and hasattr(message.forward_origin, 'chat'):
                chat_type = getattr(message.forward_origin.chat, 'type', 'chat') 
            elif has_origin and hasattr(message.forward_origin, 'sender_chat'):
                chat_type = getattr(message.forward_origin.sender_chat, 'type', 'chat')

            success_msg = f"✅ SUCCESS: The {chat_type} ID was successfully retrieved!"
    else:
        success_msg = "❌ UNABLE TO GET ID\n"
        success_msg += "Due to Telegram's API limitations, neither group ID nor user ID could be extracted."

    # SECTION 4: COMBINE ALL PARTS AND SEND

    # Check for mentions in the text (might help identify the source)
    mentioned_info = ""
    mentioned_entities = []
    if hasattr(message, 'entities') and message.entities and hasattr(message, 'text') and message.text:
        for entity in message.entities:
            if entity.type == 'mention':
                mention_text = message.text[entity.offset:entity.offset + entity.length]
                mentioned_entities.append(mention_text)

        if mentioned_entities:
            mentioned_info = f"Mentioned: {', '.join(mentioned_entities)}\n"
            mentioned_info += "⚠️ This might be related to the source group\n"

    # Combine all sections
    forward_info = f"{source_info}\n{user_info}\n"
    if mentioned_info:
        forward_info += f"{mentioned_info}\n"
    forward_info += success_msg

    # Use the appropriate keyboard
    keyboard = InlineKeyboardMarkup(row_width=2)

    if success:
        keyboard.add(
            InlineKeyboardButton(text="ℹ️ More Info", callback_data="get_info"),
            InlineKeyboardButton(text="❓ Help", callback_data="show_help")
        )
        await message.reply(forward_info, parse_mode="HTML", reply_markup=keyboard)
    else:
        keyboard.add(
            InlineKeyboardButton(text="❓ Why can't I get the ID?", callback_data="group_id_help"),
            InlineKeyboardButton(text="📚 Help", callback_data="show_help")
        )
        await message.reply(forward_info, parse_mode="HTML", reply_markup=keyboard)

async def forward_handler(message: types.Message):
    """Handler for forwarded messages - detects the original chat ID or user ID"""
    # First log all message details for debugging
    logger.info(f"=== FORWARD DEBUG INFO ===")
    logger.info(f"Message ID: {message.message_id}")
    logger.info(f"From User: {message.from_user.id} - {getattr(message.from_user, 'username', 'No username')}")
    logger.info(f"Chat: {message.chat.id} ({message.chat.type})")
    logger.info(f"Text: {message.text if hasattr(message, 'text') and message.text else 'No text'}")
    logger.info(f"Has forward_from: {message.forward_from is not None}")
    logger.info(f"Has forward_from_chat: {message.forward_from_chat is not None}")
    logger.info(f"Has forward_from_message_id: {getattr(message, 'forward_from_message_id', None) is not None}")
    logger.info(f"Has forward_signature: {getattr(message, 'forward_signature', None) is not None}")
    logger.info(f"Has forward_sender_name: {getattr(message, 'forward_sender_name', None) is not None}")
    logger.info(f"Has forward_date: {getattr(message, 'forward_date', None) is not None}")

    # Log ALL attributes of the message
    logger.info(f"Message dir: {dir(message)}")

    # Try to serialize the full message
    try:
        if hasattr(message, 'to_python'):
            logger.info(f"Message full data: {message.to_python()}")
        elif hasattr(message, 'as_json'):
            logger.info(f"Message JSON: {message.as_json()}")
        else:
            logger.info(f"Could not serialize message, no method available")
    except Exception as e:
        logger.error(f"Error serializing message: {e}")

    # Check if message has entities (like @mentions)
    if hasattr(message, 'entities') and message.entities:
        logger.info(f"Has entities: {len(message.entities)}")
        for i, entity in enumerate(message.entities):
            entity_type = getattr(entity, 'type', 'unknown')
            entity_text = message.text[entity.offset:entity.offset + entity.length] if hasattr(message, 'text') and message.text else 'N/A'
            logger.info(f"Entity {i}: type={entity_type}, text={entity_text}")

    # Check if message has forward_origin attribute and log what's inside
    if hasattr(message, 'forward_origin'):
        logger.info(f"Has forward_origin: True")
        logger.info(f"forward_origin type: {type(message.forward_origin)}")
        logger.info(f"forward_origin attributes: {dir(message.forward_origin)}")
        logger.info(f"forward_origin type attr: {getattr(message.forward_origin, 'type', 'unknown')}")

        # Try to extract more info from forward_origin
        if hasattr(message.forward_origin, 'sender_user'):
            logger.info(f"forward_origin has sender_user: {message.forward_origin.sender_user.id}")
        if hasattr(message.forward_origin, 'chat'):
            logger.info(f"forward_origin has chat: {message.forward_origin.chat.id}")
        if hasattr(message.forward_origin, 'sender_chat'):
            logger.info(f"forward_origin has sender_chat: {message.forward_origin.sender_chat.id}")
    else:
        logger.info(f"Has forward_origin: False")

    logger.info(f"=== END DEBUG INFO ===")

    # Create a nice formatted response with inline button options
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="ℹ️ More Info", callback_data="get_info"),
        InlineKeyboardButton(text="❓ Help", callback_data="show_help")
    )

    # Check for forward_origin with chat information (handles both channels and groups)
    if (hasattr(message, 'forward_origin') and 
        getattr(message.forward_origin, 'type', None) in ['channel', 'group', 'supergroup'] and 
        hasattr(message.forward_origin, 'chat')):

        # Extract chat info from forward_origin.chat
        forward_chat = message.forward_origin.chat
        forward_chat_id = forward_chat.id
        forward_chat_type = getattr(forward_chat, 'type', 'channel')
        forward_chat_title = getattr(forward_chat, 'title', 'Unknown')

        # Log the detection of a forward from a channel via forward_origin
        logger.info(f"Forwarded message detected from forward_origin.chat: {forward_chat_id} ({forward_chat_type})")

        # Build response with the available information
        forward_info = (
            f"📨 <b>Forwarded Message Info</b>\n\n"
            f"🆔 <b>Original Chat ID</b>: <code>{forward_chat_id}</code>\n"
            f"📋 <b>Chat Type</b>: {forward_chat_type}\n"
        )

        # Add title for channels
        forward_info += f"📢 <b>Title</b>: {forward_chat_title}\n"

        # Add username if available
        username = getattr(forward_chat, 'username', None)
        if username:
            forward_info += f"👤 <b>Username</b>: @{username}\n"
            forward_info += f"🔗 <b>Link</b>: https://t.me/{username}\n"

            # Add message ID if available
            if getattr(message.forward_origin, 'message_id', None):
                forward_info += f"🔢 <b>Original Message ID</b>: {message.forward_origin.message_id}\n"
                forward_info += f"🔗 <b>Original Message Link</b>: https://t.me/{username}/{message.forward_origin.message_id}\n"

        forward_info += f"\n✅ <b>SUCCESS</b>: The full {forward_chat_type.lower()} ID was successfully retrieved!"

        await message.reply(
            forward_info,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    # First case: message from a chat via forward_from_chat (traditional way)
    elif message.forward_from_chat:
        forward_from_chat = message.forward_from_chat
        forward_chat_id = forward_from_chat.id
        forward_chat_type = forward_from_chat.type
        forward_chat_title = getattr(forward_from_chat, 'title', 'Unknown')

        # Log the detection
        logger.info(f"Forwarded message detected from chat: {forward_chat_id} ({forward_chat_type})")

        # Build more detailed message when possible
        forward_info = (
            f"📨 <b>Forwarded Message Info</b>\n\n"
            f"🆔 <b>Original Chat ID</b>: <code>{forward_chat_id}</code>\n"
            f"📋 <b>Chat Type</b>: {forward_chat_type}\n"
        )

        # Add title for groups/channels
        if forward_chat_type in ['group', 'supergroup', 'channel']:
            forward_info += f"📢 <b>Title</b>: {forward_chat_title}\n"

        # Add username if available
        if getattr(forward_from_chat, 'username', None):
            forward_info += f"👤 <b>Username</b>: @{forward_from_chat.username}\n"
            forward_info += f"🔗 <b>Link</b>: https://t.me/{forward_from_chat.username}\n"

        # Add original message ID if available
        if message.forward_from_message_id:
            forward_info += f"🔢 <b>Original Message ID</b>: {message.forward_from_message_id}\n"

            # Add link to the original message if username is available
            if getattr(forward_from_chat, 'username', None):
                forward_info += f"🔗 <b>Original Message Link</b>: https://t.me/{forward_from_chat.username}/{message.forward_from_message_id}\n"

        forward_info += f"\n✅ <b>SUCCESS</b>: The full group/channel ID was successfully retrieved!"

        await message.reply(
            forward_info,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    # Second case: message from a user
    elif message.forward_from:
        forward_from = message.forward_from
        forward_user_id = forward_from.id

        # Log the detection
        logger.info(f"Forwarded message detected from user: {forward_user_id}")

        # Build user information
        forward_info = (
            f"📨 <b>Forwarded Message Info</b>\n\n"
            f"🆔 <b>Original User ID</b>: <code>{forward_user_id}</code>\n"
            f"📋 <b>Type</b>: User\n"
        )

        # Add name information
        name_parts = []
        if getattr(forward_from, 'first_name', None):
            name_parts.append(forward_from.first_name)
        if getattr(forward_from, 'last_name', None):
            name_parts.append(forward_from.last_name)

        if name_parts:
            forward_info += f"👤 <b>Name</b>: {' '.join(name_parts)}\n"

        # Add username if available
        if getattr(forward_from, 'username', None):
            forward_info += f"👤 <b>Username</b>: @{forward_from.username}\n"
            forward_info += f"🔗 <b>Profile Link</b>: https://t.me/{forward_from.username}\n"

        # Check if the message text contains mentions or text_mentions (users without username)
        mentioned_entities = []
        text_mentioned_users = []
        if hasattr(message, 'entities') and message.entities and hasattr(message, 'text') and message.text:
            for entity in message.entities:
                if entity.type == 'mention':
                    mention_text = message.text[entity.offset:entity.offset + entity.length]
                    mentioned_entities.append(mention_text)
                elif entity.type == 'text_mention' and hasattr(entity, 'user'):
                    user = entity.user
                    user_text = message.text[entity.offset:entity.offset + entity.length]
                    user_info = f"{user_text} (ID: {user.id})"
                    text_mentioned_users.append(user_info)

            if mentioned_entities:
                forward_info += f"\n📢 <b>Mentioned</b>: {', '.join(mentioned_entities)}\n"

            if text_mentioned_users:
                forward_info += f"\n👤 <b>Text Mentioned Users</b>: {', '.join(text_mentioned_users)}\n"

            if mentioned_entities or text_mentioned_users:
                forward_info += f"⚠️ <i>Note: To get complete information about these groups/users, you need to forward a message directly from them.</i>\n"

        await message.reply(
            forward_info,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    # Third case: hidden user (privacy settings restrict forwarding)
    elif hasattr(message, 'forward_sender_name') and message.forward_sender_name:
        logger.info(f"Forwarded message with hidden sender detected")

        forward_info = (
            f"📨 <b>Forwarded Message Info</b>\n\n"
            f"❌ <b>UNABLE TO GET GROUP ID</b>\n\n"
            f"ℹ️ This message was forwarded from a chat with privacy settings that restrict forwarding information.\n\n"
            f"👤 <b>Sender Name</b>: {message.forward_sender_name}\n"
            f"⚠️ <b>Chat/Group ID not available</b> due to privacy settings.\n\n"
            f"💡 <b>Solution</b>: To get the group ID, the bot needs to be added to that group first.\n"
            f"The forwarded message approach only works for public groups/channels or when the bot is already a member.\n"
        )

        # Check if the message text contains mentions or text_mentions (users without username)
        mentioned_entities = []
        text_mentioned_users = []
        if hasattr(message, 'entities') and message.entities and hasattr(message, 'text') and message.text:
            for entity in message.entities:
                if entity.type == 'mention':
                    mention_text = message.text[entity.offset:entity.offset + entity.length]
                    mentioned_entities.append(mention_text)
                elif entity.type == 'text_mention' and hasattr(entity, 'user'):
                    user = entity.user
                    user_text = message.text[entity.offset:entity.offset + entity.length]
                    user_info = f"{user_text} (ID: {user.id})"
                    text_mentioned_users.append(user_info)

            if mentioned_entities:
                forward_info += f"\n📢 <b>Mentioned</b>: {', '.join(mentioned_entities)}\n"

            if text_mentioned_users:
                forward_info += f"\n👤 <b>Text Mentioned Users</b>: {', '.join(text_mentioned_users)}\n"

            if mentioned_entities or text_mentioned_users:
                forward_info += f"⚠️ <i>Note: To get complete information about these groups/users, you need to forward a message directly from them.</i>\n"

        await message.reply(
            forward_info,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    # Fourth case: other forward types (e.g. from hidden channels)
    elif hasattr(message, 'forward_origin') and message.forward_origin:
        forward_type = getattr(message.forward_origin, 'type', 'unknown')
        logger.info(f"Forwarded message with origin type '{forward_type}' detected")

        # Create a basic response for any other forward type
        forward_info = (
            f"📨 <b>Forwarded Message Info</b>\n\n"
            f"🔍 <b>Origin Type</b>: {forward_type}\n"
        )

        # Try to extract any available information from the forward_origin
        if hasattr(message.forward_origin, 'sender_user'):
            sender = message.forward_origin.sender_user
            forward_info += f"🆔 <b>User ID</b>: <code>{sender.id}</code>\n"

            if getattr(sender, 'username', None):
                forward_info += f"👤 <b>Username</b>: @{sender.username}\n"

            name_parts = []
            if getattr(sender, 'first_name', None):
                name_parts.append(sender.first_name)
            if getattr(sender, 'last_name', None):
                name_parts.append(sender.last_name)

            if name_parts:
                forward_info += f"👤 <b>Name</b>: {' '.join(name_parts)}\n"

        # Handle sender_chat (important for group/supergroup/channel forwards)
        if hasattr(message.forward_origin, 'sender_chat') and message.forward_origin.sender_chat:
            chat = message.forward_origin.sender_chat
            forward_info += f"🆔 <b>Chat ID</b>: <code>{chat.id}</code>\n"
            chat_type = getattr(chat, 'type', 'unknown')
            forward_info += f"📋 <b>Chat Type</b>: {chat_type}\n"

            if getattr(chat, 'title', None):
                forward_info += f"📢 <b>Title</b>: {chat.title}\n"

            if getattr(chat, 'username', None):
                forward_info += f"👤 <b>Username</b>: @{chat.username}\n"
                forward_info += f"🔗 <b>Link</b>: https://t.me/{chat.username}\n"

            forward_info += f"\n✅ <b>SUCCESS</b>: The full {chat_type.lower()} ID was successfully retrieved!"

        # Handle chat in forward_origin (alternative way)
        elif hasattr(message.forward_origin, 'chat'):
            chat = message.forward_origin.chat
            forward_info += f"🆔 <b>Chat ID</b>: <code>{chat.id}</code>\n"
            chat_type = getattr(chat, 'type', 'unknown')
            forward_info += f"📋 <b>Chat Type</b>: {chat_type}\n"

            if getattr(chat, 'title', None):
                forward_info += f"📢 <b>Title</b>: {chat.title}\n"

            if getattr(chat, 'username', None):
                forward_info += f"👤 <b>Username</b>: @{chat.username}\n"
                forward_info += f"🔗 <b>Link</b>: https://t.me/{chat.username}\n"

            forward_info += f"\n✅ <b>SUCCESS</b>: The full {chat_type.lower()} ID was successfully retrieved!"

        # Check if the message text contains mentions or text_mentions (users without username)
        mentioned_entities = []
        text_mentioned_users = []
        if hasattr(message, 'entities') and message.entities and hasattr(message, 'text') and message.text:
            for entity in message.entities:
                if entity.type == 'mention':
                    mention_text = message.text[entity.offset:entity.offset + entity.length]
                    mentioned_entities.append(mention_text)
                elif entity.type == 'text_mention' and hasattr(entity, 'user'):
                    user = entity.user
                    user_text = message.text[entity.offset:entity.offset + entity.length]
                    user_info = f"{user_text} (ID: {user.id})"
                    text_mentioned_users.append(user_info)

            if mentioned_entities:
                forward_info += f"\n📢 <b>Mentioned</b>: {', '.join(mentioned_entities)}\n"

            if text_mentioned_users:
                forward_info += f"\n👤 <b>Text Mentioned Users</b>: {', '.join(text_mentioned_users)}\n"

        forward_info += f"\n⚠️ <i>Note: Some information may be hidden due to privacy settings.</i>"

        await message.reply(
            forward_info,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    # Default case: if none of the above conditions are met but it's still a forwarded message
    else:
        logger.info(f"Forwarded message detected but couldn't identify a specific forward type")

        # Get any available date info
        forward_date = getattr(message, 'forward_date', None)
        date_str = forward_date.strftime("%Y-%m-%d %H:%M UTC") if forward_date else "Unknown"

        # Create a more detailed and helpful response
        forward_info = (
            f"📨 <b>Forwarded Message Info</b>\n\n"
            f"❌ <b>UNABLE TO GET GROUP ID</b>\n\n"
            f"⚠️ This message appears to be forwarded, but the original source information is not available due to one of the following reasons:\n\n"
            f"1️⃣ The source chat has privacy settings that hide forwarded information\n"
            f"2️⃣ The bot is not a member of the source group/channel\n"
            f"3️⃣ The forwarded message is from a private chat with restrictive settings\n\n"
            f"📅 <b>Forward Date</b>: {date_str}\n"
            f"💬 <b>Message Type</b>: {message.content_type}\n\n"
            f"💡 <b>How to Get Group ID:</b>\n"
            f"- <b>Option 1:</b> Add this bot to the target group/channel\n"
            f"- <b>Option 2:</b> For public groups/channels, forward a message directly from the group/channel\n"
            f"- <b>Option 3:</b> For channels with signature, check if the original author is mentioned\n\n"
            f"ℹ️ <i>Telegram's privacy features sometimes prevent getting group IDs via forwarded messages unless the bot is a member of that group.</i>"
        )

        await message.reply(
            forward_info,
            parse_mode="HTML",
            reply_markup=keyboard
        )

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
        # Bot was mentioned, send full detailed info
        logger.info(f"Bot was mentioned in chat: {chat_id}")

        try:
            # Get full chat info
            chat_info = await get_chat_info(message.bot, chat_id)
            formatted_info = format_chat_info(chat_info)

            # Add forum topic detection if this is a forum
            if chat_info.get('is_forum'):
                from bot.utils import detect_topic_from_message
                topic_info = detect_topic_from_message(message)

                if topic_info.get('topic_id'):
                    formatted_info += f"\n\n🎯 <b>Current Topic ID</b>: {topic_info['topic_id']}"
                    formatted_info += f"\n\n💡 <b>Tip</b>: Use /info for detailed information or /topics for forum-specific details"
                else:
                    formatted_info += f"\n\n💡 <b>Tip</b>: Use /topics for forum-specific details"

            # Create inline keyboard with command buttons
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton(text="👮‍♂️ Admins", callback_data="get_admins"),
                InlineKeyboardButton(text="❓ Help", callback_data="show_help")
            )

            await message.reply(
                f"🤖 <b>Chat Information</b>\n\n{formatted_info}",
                parse_mode="HTML",
                reply_markup=keyboard
            )

        except Exception as e:
            logger.error(f"Error getting full chat info on mention: {e}")

            # Fallback to basic info if there's an error
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton(text="ℹ️ More Info", callback_data="get_info"),
                InlineKeyboardButton(text="❓ Help", callback_data="show_help")
            )

            await message.reply(
                f"🤖 <b>Chat Info</b>:\n"
                f"🆔 <b>Chat ID</b>: <code>{chat_id}</code>\n"
                f"📋 <b>Type</b>: {chat_type}\n\n"
                f"Use /info for more details.",
                parse_mode="HTML",
                reply_markup=keyboard
            )

async def button_callback(callback_query: types.CallbackQuery):
    """Handler for inline button callbacks"""
    chat_id = callback_query.message.chat.id
    action = callback_query.data

    try:
        if action == "group_id_help":
            # Provide detailed technical explanation about group IDs
            detailed_explanation = (
                "<b>📚 Technical Explanation: Group ID Limitations</b>\n\n"
                "When you forward a message from a public group, Telegram deliberately "
                "hides the source group ID for privacy reasons. This is part of Telegram's API design.\n\n"
                "<b>Why this happens:</b>\n"
                "• Public groups with privacy settings can hide their messages' origin\n"
                "• Only channels and private groups fully expose their ID in forwards\n"
                "• This protection prevents tracking and data collection across groups\n\n"
                "<b>Technical alternatives:</b>\n"
                "• If the group has a @username, you can use that in API calls\n"
                "• Bot API accepts usernames (e.g. @group_name) in most places where chat_id is needed\n"
                "• For admin-only actions, join the group with the bot first\n\n"
                "This behavior is by design in Telegram's architecture and not a limitation of this bot."
            )

            # The help info is sent as a new message (reply), not replacing the original
            await callback_query.message.reply(detailed_explanation, parse_mode="HTML")
            await callback_query.answer("Technical explanation provided")

        elif action == "get_id":
            # Create back button
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(text="« Back", callback_data="show_help"))

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
            keyboard.add(InlineKeyboardButton(text="« Back", callback_data="show_help"))

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
            keyboard.add(InlineKeyboardButton(text="« Back", callback_data="show_help"))

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
            keyboard.add(InlineKeyboardButton(text="« Back", callback_data="show_help"))

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

                # Create back button - always use show_help which handles forum detection
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton(text="« Back", callback_data="show_help"))

                # Send the formatted admin info
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
                keyboard.add(InlineKeyboardButton(text="« Back", callback_data="show_help"))

                await callback_query.message.edit_text(
                    f"❌ Error getting administrator information: {str(e)}",
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

        elif action == "get_topics":
            try:
                # Check if this is a forum
                chat = await callback_query.bot.get_chat(chat_id)
                if hasattr(chat, 'is_forum') and chat.is_forum:
                    from bot.utils import detect_topic_from_message
                    topic_info = detect_topic_from_message(callback_query.message)

                    response = f"📝 <b>Forum Topics Information</b>\n\n"
                    response += f"🆔 <b>Chat ID</b>: <code>{chat_id}</code>\n"
                    response += f"📊 <b>Is Forum</b>: Yes\n"
                    response += f"📢 <b>Title</b>: {chat.title}\n\n"

                    if topic_info.get('topic_id'):
                        response += f"🎯 <b>Current Topic ID</b>: <code>{topic_info['topic_id']}</code>\n"
                        response += f"📍 <b>You are currently in topic ID {topic_info['topic_id']}</b>\n\n"
                    else:
                        response += f"📍 <b>General Topic</b> (no specific topic ID)\n\n"

                    response += f"💡 <b>Note</b>: This bot can detect the current topic ID when you interact from within a specific topic. "
                    response += f"To get topic IDs from other topics, use /topics command from those topics.\n\n"
                    response += f"🔧 <b>For Developers</b>: Use the topic ID as the message_thread_id when sending messages to specific topics via the Bot API."
                else:
                    response = f"📝 <b>Forum Topics</b>\n\n"
                    response += f"This chat is not a forum supergroup. Forum topics are only available in forum-enabled supergroups.\n\n"
                    response += f"To use forum features:\n"
                    response += f"1. Create or convert a supergroup to a forum\n" 
                    response += f"2. Enable 'Topics' in the group settings\n"
                    response += f"3. Add this bot to the forum group"

                # Create back button
                keyboard = InlineKeyboardMarkup(row_width=1)
                keyboard.add(InlineKeyboardButton(text="« Back", callback_data="show_help"))

                await callback_query.message.edit_text(
                    response,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

            except Exception as e:
                logger.error(f"Error getting topics info: {e}")

                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton(text="« Back", callback_data="show_help"))

                await callback_query.message.edit_text(
                    f"❌ Error getting topic information: {str(e)}",
                    reply_markup=keyboard
                )

        elif action == "group_id_help":
            # Provide detailed help about group ID limitations
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(text="« Back", callback_data="show_help"))

            explanation = (
                "<b>📚 Why Can't I Get Group IDs from Forwards?</b>\n\n"
                "This is a common issue with Telegram's privacy design:\n\n"
                "<b>Technical Explanation:</b>\n"
                "• When forwarding from public groups, Telegram intentionally hides the original group ID\n"
                "• The forward appears to come from the original sender (user) instead of the group\n"
                "• This is a privacy feature by design, not a limitation of this bot\n"
                "• Even in forwards from public groups, Telegram only shows user information\n\n"

                "<b>Why This Happens:</b>\n"
                "Telegram does this to prevent tracking and data collection across groups. Only bot developers "
                "who add their bots to groups can access group IDs directly.\n\n"

                "<b>Solutions:</b>\n"
                "1️⃣ <b>Add this bot directly to the group</b> (recommended)\n"
                "2️⃣ For public groups, use @username instead of ID in API calls\n"
                "3️⃣ For user accounts (not bots), open forwarded message in Telegram apps and look for the source group link\n"
                "4️⃣ For private groups, add this bot as member\n\n"

                "If you need more technical explanations, feel free to ask!"
            )

            await callback_query.message.edit_text(
                explanation,
                parse_mode="HTML",
                reply_markup=keyboard
            )

        elif action == "show_help":
            # Recreate the help keyboard  
            keyboard = InlineKeyboardMarkup(row_width=2)

            # Use simpler forum detection from message object instead of async call
            is_forum = hasattr(callback_query.message.chat, 'is_forum') and callback_query.message.chat.is_forum

            if is_forum:
                keyboard.add(
                    InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                    InlineKeyboardButton(text="ℹ️ Chat Info", callback_data="get_info"),
                    InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
                    InlineKeyboardButton(text="👥 Members", callback_data="get_members"),
                    InlineKeyboardButton(text="📝 Topics", callback_data="get_topics"),
                    InlineKeyboardButton(text="👮‍♂️ Admins", callback_data="get_admins"),
                    InlineKeyboardButton(text="❓ Group ID Help", callback_data="group_id_help")
                )
            else:
                keyboard.add(
                    InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                    InlineKeyboardButton(text="ℹ️ Chat Info", callback_data="get_info"),
                    InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
                    InlineKeyboardButton(text="👥 Members", callback_data="get_members"),
                    InlineKeyboardButton(text="👮‍♂️ Admins", callback_data="get_admins"),
                    InlineKeyboardButton(text="❓ Group ID Help", callback_data="group_id_help")
                )

            help_text = (
                "🔍 <b>Available Commands</b>:\n\n"
                "/id - Get the current chat ID\n"
                "/info - Display detailed information about this chat\n"
                "/hello - Force the bot to respond with basic chat info\n"
                "/type - Show the chat type (private, group, supergroup, channel)\n"
                "/members - Get the number of members (when available)\n"
                "/topics - Show forum topic information (for forum supergroups)\n"
                "/admins - Get information about group administrators\n"
                "/forward_help - Explain why group IDs from forwards sometimes don't work\n\n"
                "📨 <b>Get Group/Channel IDs</b>:\n"
                "<b>Method 1 (Recommended)</b>: Add me to the group/channel and use /id command.\n"
                "<b>Method 2</b>: Forward a message from a public group/channel, and I'll show the source chat ID.\n\n"
                "❓ <b>Trouble getting group IDs?</b> Use the Group ID Help button below.\n\n"
                "You can also @mention me in a message to get basic chat info.\n\n"
                "<i>Note: Some information may be limited based on my permissions and the chat type.</i>"
            )

            try:
                await callback_query.message.edit_text(
                    help_text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Error editing message in show_help: {e}")
                logger.exception("Full exception:")
            finally:
                # Always answer the callback query to remove loading state
                await callback_query.answer()

        else:
            # Answer the callback query to remove the loading indicator for other actions
            await callback_query.answer()

    except Exception as e:
        logger.error(f"Error handling button callback: {e}")
        await callback_query.answer(f"Error: {str(e)[:200]}")  # Limit error message length