from dotenv import load_dotenv
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.fsm.storage.redis import DefaultKeyBuilder, Redis, RedisStorage

from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode, setup_dialogs

from configparser import ConfigParser

from dialogs.auth import auth_dialog, AuthDialogSG
from middleware import DatabaseMiddleware

# Читаем конфигурацию
load_dotenv()
config = ConfigParser()
config.read('mslu-bot.ini')

API_TOKEN = os.getenv('bot_id')

# EIOS
server = config.get('Database', 'DbServer')
database = config.get('Database', 'DatabaseName')
driver = config.get('Database', 'DriverName')
# ldap
ldap_server = config.get('LDAP', 'server')

eios = None

# Redis
redis_server = config.get('Redis', 'ServerName')
redis_port = int(config.get('Redis', 'Port'))
redis_base_info = int(config.get('Redis', 'Base'))
redis_base_fsm = int(config.get('Redis', 'Fsm'))
redis_info = Redis(  host=redis_server,   port=redis_port,   db=redis_base_info)
redis_fsm = Redis(  host=redis_server,   port=redis_port,   db=redis_base_fsm)

storage = RedisStorage(redis=redis_fsm, key_builder=DefaultKeyBuilder(with_destiny=True))

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=storage)


@dp.message(CommandStart())
async def command_start_process(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=AuthDialogSG.start, mode=StartMode.RESET_STACK)


if __name__ == '__main__':
    dp.include_router(auth_dialog)
    dp.update.middleware(DatabaseMiddleware(eios, redis_info, ldap_server))
    setup_dialogs(dp)
    dp.run_polling(bot)
