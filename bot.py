import asyncio
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from db import init_db
from handlers import user, admin
from notifications import (
    send_daily_report_and_clear, 
    send_tomorrow_admin_report, 
    send_2h_reminders
)


async def main():
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_daily_report_and_clear, "cron", hour=23, minute=0, args=[bot])
    scheduler.add_job(send_tomorrow_admin_report, "cron", hour=23, minute=0, args=[bot])
    scheduler.add_job(send_2h_reminders, "cron", hour='9-23', minute=30, args=[bot])
    scheduler.start()

    dp.include_router(admin.router)
    dp.include_router(user.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())