from os import getenv

admin_chat = getenv('ADMIN_CHAT')
if admin_chat is None: 
    raise ValueError('ADMIN_CHAT environment variable can not be None')
admin_chat = int(admin_chat)

token_bot = getenv('TOKEN_BOT')
if token_bot is None: 
    raise ValueError('TOKEN_BOT environment variable can not be None')
