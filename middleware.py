from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, db, redis, ldap_server) -> None:
        self.db = db
        self.redis = redis
        self.ldap_server = ldap_server

    async def __call__( self, 
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject, 
        data: Dict[str, Any]) -> Any:
            data['eios'] = self.db
            data['redis'] = self.redis
            data['ldap_server'] = self.ldap_server
            return await handler(event, data)
