from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import json
from datetime import datetime

api_id = '31465038'
api_hash = '87a2e28b8255c65ed7c917005d4ba94c'
phone = '+79115045294'

client = TelegramClient('session_name', api_id, api_hash)

async def parse_chat_to_json(chat_entity, limit=10**4):
    """Parse chat messages to JSON"""
    
    messages_data = []
    
    async for message in client.iter_messages(chat_entity, limit=limit):
        msg_data = {
            'id': message.id,
            'date': message.date.isoformat() if message.date else None,
            'sender_id': message.sender_id,
            'text': message.text or message.message,
            'raw_text': message.raw_text,
            'is_reply': message.is_reply,
            'reply_to_msg_id': message.reply_to.reply_to_msg_id if message.reply_to else None,
            'views': message.views,
            'forwards': message.forwards,
            'edit_date': message.edit_date.isoformat() if message.edit_date else None,
            'post': message.post,
            'silent': message.silent,
            'media': None,
            'entities': [],
            'reactions': []
        }
        
        if message.sender:
            msg_data['sender'] = {
                'id': message.sender.id,
                'first_name': getattr(message.sender, 'first_name', ''),
                'last_name': getattr(message.sender, 'last_name', ''),
                'username': message.sender.username,
                'phone': getattr(message.sender, 'phone', '')
            }
        
        # Parse message entities (bold, italic, links, etc.)
        if message.entities:
            msg_data['entities'] = [
                {
                    'type': str(entity.__class__.__name__),
                    'offset': entity.offset,
                    'length': entity.length,
                    'url': getattr(entity, 'url', None)
                }
                for entity in message.entities
            ]
        
        messages_data.append(msg_data)
    
    return messages_data

async def main():
    await client.start(phone)
    
    # You can get chat by:
    # 1. Username
    chat = await client.get_entity('igrebenkin')
    
    # 2. Chat ID (use negative for groups/channels)
    # chat = await client.get_entity(-1001234567890)
    
    # 3. Phone number (for private chats)
    # chat = await client.get_entity('+1234567890')
    
    # Parse messages (adjust limit as needed)
    messages = await parse_chat_to_json(chat, limit=10**5)
    
    # Save to JSON file
    with open('telegram_messages.json', 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(messages)} messages to telegram_messages.json")
    
    with open('messages_readable.txt', 'w', encoding='utf-8') as f:
        for msg in messages:
            f.write(f"\n[{msg['date']}] {msg.get('sender', {}).get('username', 'Unknown')}:\n")
            f.write(f"{msg['text']}\n")
            f.write("-" * 50 + "\n")

# Run the script
with client:
    client.loop.run_until_complete(main())