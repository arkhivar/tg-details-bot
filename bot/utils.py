import logging
from datetime import datetime
from aiogram import Bot
from aiogram.utils.exceptions import ChatNotFound, Unauthorized

logger = logging.getLogger(__name__)

async def get_chat_info(bot: Bot, chat_id):
    """
    Get detailed information about a chat.
    
    Args:
        bot: Aiogram Bot instance
        chat_id: The ID of the chat
        
    Returns:
        dict: Chat information
    """
    try:
        chat = await bot.get_chat(chat_id)
        
        # Create a base info dictionary
        info = {
            "id": chat.id,
            "type": chat.type,
            "title": getattr(chat, "title", None),
            "username": getattr(chat, "username", None),
            "first_name": getattr(chat, "first_name", None),
            "last_name": getattr(chat, "last_name", None),
            "description": getattr(chat, "description", None),
            "invite_link": getattr(chat, "invite_link", None),
            "members_count": getattr(chat, "members_count", None),
            "permissions": getattr(chat, "permissions", None),
            "is_forum": getattr(chat, "is_forum", None),
            "active_usernames": getattr(chat, "active_usernames", None),
            "has_restricted_voice_and_video_messages": getattr(
                chat, "has_restricted_voice_and_video_messages", None
            ),
            "join_to_send_messages": getattr(chat, "join_to_send_messages", None),
            "join_by_request": getattr(chat, "join_by_request", None),
            "has_protected_content": getattr(chat, "has_protected_content", None),
            "slow_mode_delay": getattr(chat, "slow_mode_delay", None),
            "sticker_set_name": getattr(chat, "sticker_set_name", None),
            "can_set_sticker_set": getattr(chat, "can_set_sticker_set", None),
            "linked_chat_id": getattr(chat, "linked_chat_id", None),
            "location": getattr(chat, "location", None),
        }

        # Add the chat photo info if available
        if hasattr(chat, "photo") and chat.photo:
            info["has_photo"] = True
        else:
            info["has_photo"] = False
        
        return info
    
    except ChatNotFound:
        logger.error(f"Chat {chat_id} not found")
        raise Exception(f"Chat {chat_id} not found")
    
    except Unauthorized:
        logger.error(f"Bot is not authorized to access chat {chat_id}")
        raise Exception(f"Bot is not authorized to access this chat")
    
    except Exception as e:
        logger.error(f"Error getting chat info: {e}")
        raise

def format_chat_info(info):
    """
    Format chat information into a readable text.
    
    Args:
        info (dict): Chat information
        
    Returns:
        str: Formatted text
    """
    sections = []
    
    # Basic Info
    basic_info = [
        f"🆔 <b>Chat ID</b>: <code>{info['id']}</code>",
        f"📋 <b>Type</b>: {info['type']}"
    ]
    
    # Add appropriate name fields
    if info['type'] == 'private':
        name_parts = []
        if info['first_name']:
            name_parts.append(info['first_name'])
        if info['last_name']:
            name_parts.append(info['last_name'])
        
        if name_parts:
            basic_info.append(f"👤 <b>Name</b>: {' '.join(name_parts)}")
    else:
        if info['title']:
            basic_info.append(f"📢 <b>Title</b>: {info['title']}")
    
    if info['username']:
        basic_info.append(f"🔗 <b>Username</b>: @{info['username']}")
    
    sections.append("\n".join(basic_info))
    
    # Additional Info
    additional_info = []
    
    if info['description']:
        additional_info.append(f"📝 <b>Description</b>: {info['description']}")
    
    if info['members_count'] is not None:
        additional_info.append(f"👥 <b>Members</b>: {info['members_count']}")
    
    if info['invite_link']:
        additional_info.append(f"🔗 <b>Invite Link</b>: {info['invite_link']}")
    
    if info['linked_chat_id']:
        additional_info.append(f"🔄 <b>Linked Chat ID</b>: <code>{info['linked_chat_id']}</code>")
    
    if additional_info:
        sections.append("\n".join(additional_info))
    
    # Technical Info
    technical_info = []
    
    if info['is_forum'] is not None:
        technical_info.append(f"📊 <b>Is Forum</b>: {info['is_forum']}")
    
    if info['slow_mode_delay'] is not None and info['slow_mode_delay'] > 0:
        technical_info.append(f"⏱ <b>Slow Mode Delay</b>: {info['slow_mode_delay']} seconds")
    
    if info['has_protected_content'] is not None:
        technical_info.append(f"🔒 <b>Protected Content</b>: {info['has_protected_content']}")
    
    if info['join_to_send_messages'] is not None:
        technical_info.append(f"✉️ <b>Join to Send Messages</b>: {info['join_to_send_messages']}")
    
    if info['join_by_request'] is not None:
        technical_info.append(f"👤 <b>Join by Request</b>: {info['join_by_request']}")
    
    if info['has_photo']:
        technical_info.append(f"🖼 <b>Has Profile Photo</b>: Yes")
    
    if technical_info:
        sections.append("\n".join(technical_info))
    
    # Current time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sections.append(f"⏰ <b>Information retrieved at</b>: {current_time}")
    
    return "\n\n".join(sections)
