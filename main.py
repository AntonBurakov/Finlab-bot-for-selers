import asyncio
from aiogram import Bot, Dispatcher

from app.handlers import router
from app.database.models import async_main


async def main():
    await async_main()
    bot = Bot(token='8059403580:AAF80PF66sSd1KWCEYKLHEH9qU6sSoun10k')   
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
