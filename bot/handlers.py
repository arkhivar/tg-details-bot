import logging
from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .utils import get_chat_info, format_chat_info, get_chat_admins, format_admin_info, detect_topic_from_message

logger = logging.getLogger(__name__)

router = Router()

ALL_CALLBACKS = {"get_id", "get_info", "get_type", "get_members", "get_admins", "get_topics", "group_id_help", "show_help"}


def register_handlers(dp):
    """
    Register message handlers for the bot.

    Args:
        dp: Aiogram dispatcher
    """
    dp.include_router(router)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

@router.message(CommandStart())
async def start_command(message: types.Message):
    """Handler for /start command"""
    chat_type = message.chat.type

    # Different response based on chat type
    if chat_type == 'private':
        # In private chats, show introduction
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                InlineKeyboardButton(text="ℹ️ Chat Info", callback_data="get_info"),
            ],
            [
                InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
                InlineKeyboardButton(text="👥 Members", callback_data="get_members"),
            ],
        ])

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

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                    InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
                ],
                [
                    InlineKeyboardButton(text="👥 Members", callback_data="get_members"),
                    InlineKeyboardButton(text="❓ Help", callback_data="show_help"),
                ],
            ])

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
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                    InlineKeyboardButton(text="❓ Help", callback_data="show_help"),
                ],
            ])

            await message.reply(
                f"👋 <b>Hello!</b> I'm a Telegram Info Bot.\n\n"
                f"<b>Chat ID:</b> <code>{message.chat.id}</code>\n"
                f"<b>Chat Type:</b> {message.chat.type}\n\n"
                f"Use /info for more details or /help to see all commands.",
                parse_mode="HTML",
                reply_markup=keyboard
            )


@router.message(Command("help"))
async def help_command(message: types.Message):
    """Handler for /help command"""
    # Create inline keyboard with command buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
            InlineKeyboardButton(text="ℹ️ Chat Info", callback_data="get_info"),
        ],
        [
            InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
            InlineKeyboardButton(text="👥 Members", callback_data="get_members"),
        ],
        [
            InlineKeyboardButton(text="👮‍♂️ Admins", callback_data="get_admins"),
            InlineKeyboardButton(text="❓ Group ID Help", callback_data="group_id_help"),
        ],
    ])

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


@router.message(Command("id"))
async def id_command(message: types.Message):
    """Handler for /id command"""
    chat_id = message.chat.id
    await message.reply(f"🆔 <b>Chat ID</b>: <code>{chat_id}</code>", parse_mode="HTML")


@router.message(Command("info"))
async def info_command(message: types.Message):
    """Handler for /info command"""
    try:
        chat_info = await get_chat_info(message.bot, message.chat.id)
        formatted_info = format_chat_info(chat_info)

        # Add forum topic detection if this is a forum
        if chat_info.get('is_forum'):
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


@router.message(Command("type"))
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


@router.message(Command("members"))
async def members_command(message: types.Message):
    """Handler for /members command"""
    try:
        if message.chat.type in ["private"]:
            await message.reply("This command only works in groups and channels.")
            return

        # Get member count via Bot API (works for groups, supergroups and channels)
        member_count = await message.bot.get_chat_member_count(message.chat.id)
        await message.reply(f"👥 <b>Member count</b>: {member_count}", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error getting members count: {e}")
        await message.reply(f"❌ Error getting member count: {str(e)}")


@router.message(Command("topics"))
async def topics_command(message: types.Message):
    """Handler for /topics command - shows forum topic information"""
    try:
        if message.chat.type in ["private"]:
            await message.reply("This command only works in groups and channels.")
            return

        # Check if this is a forum
        if getattr(message.chat, 'is_forum', False):
            # Get topic information from current message
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
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="📋 Chat ID", callback_data="get_id"),
                    InlineKeyboardButton(text="ℹ️ More Info", callback_data="get_info"),
                ],
                [
                    InlineKeyboardButton(text="❓ Help", callback_data="show_help"),
                ],
            ])

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


@router.message(Command("hello"))
async def hello_command(message: types.Message):
    """Handler for /hello command - an explicit command to get bot to respond"""
    try:
        logger.info(f"Hello command received in chat: {message.chat.id}")
        chat_id = message.chat.id
        chat_type = message.chat.type

        # Create keyboard with info buttons
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                InlineKeyboardButton(text="ℹ️ Chat Info", callback_data="get_info"),
            ],
            [
                InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
                InlineKeyboardButton(text="❓ Help", callback_data="show_help"),
            ],
        ])

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


@router.message(Command("admins"))
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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Back", callback_data="show_help")],
        ])

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


@router.message(Command("forward_help"))
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

        "If you need more technical explanations, feel free to ask!"
    )

    await message.reply(explanation, parse_mode="HTML")


# ---------------------------------------------------------------------------
# Welcome flow: bot added to a chat
# ---------------------------------------------------------------------------

@router.message(F.new_chat_members)
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
    for user in message.new_chat_members:
        logger.info(f"Checking user: {user.id} vs bot: {bot_id}")
        if user.id == bot_id:
            logger.info(f"Bot was added to chat: {message.chat.id} - {message.chat.title}")

            # Bot was added to a new chat, send info immediately
            try:
                # First, send an immediate welcome message
                initial_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                        InlineKeyboardButton(text="❓ Help", callback_data="show_help"),
                    ],
                ])

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
                    topic_info = detect_topic_from_message(message)
                    if topic_info.get('topic_id'):
                        topic_info_text = f"\n🎯 <b>Current Topic ID</b>: <code>{topic_info['topic_id']}</code>\n💡 <b>Use /topics command to get more topic information</b>\n"
                    else:
                        topic_info_text = f"\n📝 <b>Forum detected!</b> Use /topics command for topic information\n"

                formatted_info = format_chat_info(chat_info) + topic_info_text

                # Create detailed inline keyboard with command buttons
                # Add different buttons based on whether it's a forum
                if chat_info.get('is_forum'):
                    detailed_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                            InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
                        ],
                        [
                            InlineKeyboardButton(text="👥 Members", callback_data="get_members"),
                            InlineKeyboardButton(text="📝 Topics", callback_data="get_topics"),
                        ],
                        [
                            InlineKeyboardButton(text="❓ Help", callback_data="show_help"),
                        ],
                    ])
                else:
                    detailed_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                            InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
                        ],
                        [
                            InlineKeyboardButton(text="👥 Members", callback_data="get_members"),
                            InlineKeyboardButton(text="❓ Help", callback_data="show_help"),
                        ],
                    ])

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
                    simple_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                            InlineKeyboardButton(text="❓ Help", callback_data="show_help"),
                        ],
                    ])

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


# ---------------------------------------------------------------------------
# Forwarded message analysis (Bot API 7.0+ forward_origin)
# ---------------------------------------------------------------------------
# Bot API 7.0 removed the legacy forward fields (origin user/chat/date).
# All forwards now arrive with a typed `forward_origin` object:
#   - MessageOriginChannel:    .chat, .message_id, .author_signature, .date
#   - MessageOriginChat:       .sender_chat, .date
#   - MessageOriginUser:       .sender_user, .date
#   - MessageOriginHiddenUser: .sender_user_name, .date
# ---------------------------------------------------------------------------

def _extract_mention_info(message: types.Message) -> str:
    """Extract @mentions and text_mention users from a message (unchanged API in 3.x)."""
    mentioned_info = ""
    text = message.text or message.caption
    entities = message.entities or message.caption_entities
    if entities and text:
        mentioned_entities = []
        text_mentioned_users = []
        for entity in entities:
            if entity.type == 'mention':
                mentioned_entities.append(text[entity.offset:entity.offset + entity.length])
            elif entity.type == 'text_mention' and entity.user:
                user = entity.user
                user_text = text[entity.offset:entity.offset + entity.length]
                text_mentioned_users.append(f"{user_text} (ID: {user.id})")

        if mentioned_entities:
            mentioned_info += f"📢 <b>Mentioned</b>: {', '.join(mentioned_entities)}\n"
            mentioned_info += "⚠️ <i>This might be related to the source group</i>\n"

        if text_mentioned_users:
            mentioned_info += f"👤 <b>Text Mentioned Users</b>: {', '.join(text_mentioned_users)}\n"

    return mentioned_info


def _chat_block(chat: types.Chat) -> str:
    """Format a source chat (channel/group) info block."""
    chat_type = (chat.type or 'chat').upper()
    block = f"SOURCE {chat_type}: ID <code>{chat.id}</code>\n"

    if chat.title:
        block += f"📢 Title: {chat.title}\n"

    if chat.username:
        block += f"👤 Username: @{chat.username}\n"
        block += f"🔗 Link: https://t.me/{chat.username}\n"

    return block


def _success_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="ℹ️ More Info", callback_data="get_info"),
            InlineKeyboardButton(text="❓ Help", callback_data="show_help"),
        ],
    ])


def _help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❓ Why can't I get the ID?", callback_data="group_id_help"),
            InlineKeyboardButton(text="📚 Help", callback_data="show_help"),
        ],
    ])


@router.message(F.forward_origin)
async def forward_origin_handler(message: types.Message):
    """Single handler for all forwarded messages (Bot API 7.0+ forward_origin)."""
    origin = message.forward_origin
    logger.info(f"Forward detected, origin type: {origin.type} (message_id={message.message_id})")

    mentioned_info = _extract_mention_info(message)
    body = ""
    success = True

    if isinstance(origin, types.MessageOriginChannel):
        # Forward from a channel: full chat info + original message ID/link
        chat = origin.chat
        body = _chat_block(chat)
        body += f"🔢 Message ID: {origin.message_id}\n"
        if chat.username:
            body += f"🔗 Message Link: https://t.me/{chat.username}/{origin.message_id}\n"
        if origin.author_signature:
            body += f"✍️ Author signature: {origin.author_signature}\n"
        success_msg = f"✅ SUCCESS: The {chat.type} ID was successfully retrieved!"

    elif isinstance(origin, types.MessageOriginChat):
        # Anonymous admin / group-as-sender forward
        chat = origin.sender_chat
        body = _chat_block(chat)
        success_msg = f"✅ SUCCESS: The {chat.type} ID was successfully retrieved!"

    elif isinstance(origin, types.MessageOriginUser):
        # Forward from a user (Telegram shows the user, not any source group)
        user = origin.sender_user
        body = f"Forwarded from User 🆔 <code>{user.id}</code>\n"

        if user.username:
            body += f"👤 Username: @{user.username}\n"
            body += f"🔗 Link: https://t.me/{user.username}\n"

        name_parts = [p for p in (user.first_name, user.last_name) if p]
        if name_parts:
            body += f"👤 Name: {' '.join(name_parts)}\n"

        body += (
            "⚠️ <i>This is the user's ID, not a group ID. If this message was originally "
            "posted in a group, Telegram hides the group behind the user for privacy reasons "
            "(see /forward_help).</i>\n"
        )
        success_msg = "✅ SUCCESS: The user ID was successfully retrieved!"

    elif isinstance(origin, types.MessageOriginHiddenUser):
        # Privacy-protected user forward: only a name is available
        body = f"Forwarded from User: {origin.sender_user_name}\n"
        body += "⚠️ User ID not available — this user hides their account in forwarded messages (privacy setting).\n"
        success_msg = "❌ UNABLE TO GET ID\nDue to the sender's privacy settings, no ID could be extracted."
        success = False

    else:
        # Unknown/future origin type — degrade gracefully
        body = f"Origin type: {getattr(origin, 'type', 'unknown')}\n"
        body += "⚠️ Unable to retrieve source ID due to privacy settings\n"
        success_msg = "❌ UNABLE TO GET ID\nDue to Telegram's API limitations, neither group ID nor user ID could be extracted."
        success = False

    forward_info = f"{body}\n"
    if mentioned_info:
        forward_info += f"{mentioned_info}\n"
    forward_info += success_msg

    keyboard = _success_keyboard() if success else _help_keyboard()
    await message.reply(forward_info, parse_mode="HTML", reply_markup=keyboard)


# ---------------------------------------------------------------------------
# General text handler (@mention full-info flow)
# ---------------------------------------------------------------------------

@router.message(F.text)
async def message_handler(message: types.Message):
    """General message handler"""
    chat_id = message.chat.id
    chat_type = message.chat.type

    # Special handling for group chats
    if chat_type in ['group', 'supergroup'] and message.from_user:
        if message.from_user.is_bot:
            # Don't respond to other bots
            return

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
                topic_info = detect_topic_from_message(message)

                if topic_info.get('topic_id'):
                    formatted_info += f"\n\n🎯 <b>Current Topic ID</b>: {topic_info['topic_id']}"
                    formatted_info += f"\n\n💡 <b>Tip</b>: Use /info for detailed information or /topics for forum-specific details"
                else:
                    formatted_info += f"\n\n💡 <b>Tip</b>: Use /topics for forum-specific details"

            # Create inline keyboard with command buttons
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="👮‍♂️ Admins", callback_data="get_admins"),
                    InlineKeyboardButton(text="❓ Help", callback_data="show_help"),
                ],
            ])

            await message.reply(
                f"🤖 <b>Chat Information</b>\n\n{formatted_info}",
                parse_mode="HTML",
                reply_markup=keyboard
            )

        except Exception as e:
            logger.error(f"Error getting full chat info on mention: {e}")

            # Fallback to basic info if there's an error
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="ℹ️ More Info", callback_data="get_info"),
                    InlineKeyboardButton(text="❓ Help", callback_data="show_help"),
                ],
            ])

            await message.reply(
                f"🤖 <b>Chat Info</b>:\n"
                f"🆔 <b>Chat ID</b>: <code>{chat_id}</code>\n"
                f"📋 <b>Type</b>: {chat_type}\n\n"
                f"Use /info for more details.",
                parse_mode="HTML",
                reply_markup=keyboard
            )


# ---------------------------------------------------------------------------
# Inline button callbacks — every emitted callback_data MUST route here
# ---------------------------------------------------------------------------

@router.callback_query(F.data.in_(ALL_CALLBACKS))
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
            keyboard = _back_keyboard()

            await callback_query.message.edit_text(
                f"🆔 <b>Chat ID</b>: <code>{chat_id}</code>",
                parse_mode="HTML",
                reply_markup=keyboard
            )

        elif action == "get_info":
            chat_info = await get_chat_info(callback_query.bot, chat_id)
            formatted_info = format_chat_info(chat_info)

            # Create back button
            keyboard = _back_keyboard()

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

            await callback_query.message.edit_text(
                f"<b>Chat Type</b>: {chat_type}\n{type_description}",
                parse_mode="HTML",
                reply_markup=_back_keyboard()
            )

        elif action == "get_members":
            if callback_query.message.chat.type in ["private"]:
                await callback_query.answer("This feature only works in groups and channels")
                return

            # Get member count via Bot API (works for groups, supergroups and channels)
            member_count = await callback_query.bot.get_chat_member_count(chat_id)
            await callback_query.message.edit_text(
                f"👥 <b>Member count</b>: {member_count}",
                parse_mode="HTML",
                reply_markup=_back_keyboard()
            )

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

                # Send the formatted admin info
                await callback_query.message.edit_text(
                    formatted_info,
                    parse_mode="HTML",
                    reply_markup=_back_keyboard()
                )
            except Exception as e:
                logger.error(f"Error getting admin information via callback: {e}")
                logger.exception("Full exception details:")

                await callback_query.message.edit_text(
                    f"❌ Error getting administrator information: {str(e)}",
                    parse_mode="HTML",
                    reply_markup=_back_keyboard()
                )

        elif action == "get_topics":
            try:
                # Check if this is a forum
                chat = await callback_query.bot.get_chat(chat_id)
                if getattr(chat, 'is_forum', False):
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

                await callback_query.message.edit_text(
                    response,
                    parse_mode="HTML",
                    reply_markup=_back_keyboard()
                )

            except Exception as e:
                logger.error(f"Error getting topics info: {e}")

                await callback_query.message.edit_text(
                    f"❌ Error getting topic information: {str(e)}",
                    parse_mode="HTML",
                    reply_markup=_back_keyboard()
                )

        elif action == "show_help":
            # First, immediately answer the callback to remove loading state
            try:
                await callback_query.answer()
            except Exception:
                pass

            # Use simpler forum detection from message object instead of async call
            is_forum = getattr(callback_query.message.chat, 'is_forum', False)

            if is_forum:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                        InlineKeyboardButton(text="ℹ️ Chat Info", callback_data="get_info"),
                    ],
                    [
                        InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
                        InlineKeyboardButton(text="👥 Members", callback_data="get_members"),
                    ],
                    [
                        InlineKeyboardButton(text="📝 Topics", callback_data="get_topics"),
                        InlineKeyboardButton(text="👮‍♂️ Admins", callback_data="get_admins"),
                    ],
                    [
                        InlineKeyboardButton(text="❓ Group ID Help", callback_data="group_id_help"),
                    ],
                ])
            else:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="📋 Get Chat ID", callback_data="get_id"),
                        InlineKeyboardButton(text="ℹ️ Chat Info", callback_data="get_info"),
                    ],
                    [
                        InlineKeyboardButton(text="📊 Chat Type", callback_data="get_type"),
                        InlineKeyboardButton(text="👥 Members", callback_data="get_members"),
                    ],
                    [
                        InlineKeyboardButton(text="👮‍♂️ Admins", callback_data="get_admins"),
                        InlineKeyboardButton(text="❓ Group ID Help", callback_data="group_id_help"),
                    ],
                ])

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

            # Edit the message - wrap in try/except
            try:
                await callback_query.message.edit_text(
                    help_text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Error editing message in show_help: {e}")
                logger.exception("Full exception:")

        else:
            # Answer the callback query to remove the loading indicator for other actions
            await callback_query.answer()

    except Exception as e:
        logger.error(f"Error handling button callback: {e}")
        await callback_query.answer(f"Error: {str(e)[:200]}")  # Limit error message length


def _back_keyboard() -> InlineKeyboardMarkup:
    """Single « Back button keyboard (routes to show_help)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Back", callback_data="show_help")],
    ])
