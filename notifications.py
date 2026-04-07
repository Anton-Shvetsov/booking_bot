import asyncio
from logger_config import logger
from datetime import datetime, timedelta, date
from aiogram import Bot

from config import ADMIN_IDS
from db import get_bookings_for_day, clear_day_data, get_bookings_in_time_range


def escape_md(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)


async def send_daily_report_and_clear(bot: Bot):
    today = date.today()
    bookings = await get_bookings_for_day(today)
    
    if not bookings:
        report = f"📅 Итоговый отчет за {today.strftime('%d.%m')}:\nЗаписей не было."
    else:
        report = f"📅 **Итоговый отчет за {today.strftime('%d.%m')}**:\n\n"
        for start_time_iso, user_info in bookings:
            time_str = datetime.fromisoformat(start_time_iso).strftime("%H:%M")
            user_info = escape_md(user_info)
            report += f"✅ {time_str} — {user_info}\n"
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, report, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Не удалось отправить отчет за сегодня {admin_id}")
            
    await clear_day_data(today)


async def send_tomorrow_admin_report(bot: Bot):
    tomorrow = date.today() + timedelta(days=1)
    bookings = await get_bookings_for_day(tomorrow)
    
    header = f"🔮 **План на завтра ({tomorrow.strftime('%d.%m')})**:\n\n"
    
    if not bookings:
        text = header + "Записей пока нет."
    else:
        lines = []
        for start_time_iso, user_info in bookings:
            time_str = datetime.fromisoformat(start_time_iso).strftime("%H:%M")
            user_info = escape_md(user_info)
            lines.append(f"📌 {time_str} — {user_info}")
        text = header + "\n".join(lines)
        
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="Markdown")
        except Exception:
            logger.error(f"Не удалось отправить план на завтра {admin_id}")


async def send_2h_reminders(bot: Bot):
    now = datetime.now()
    target_time = now + timedelta(hours=2)
    
    start_range = target_time.replace(minute=28, second=0, microsecond=0)
    end_range = target_time.replace(minute=33, second=0, microsecond=0)
    
    bookings = await get_bookings_in_time_range(start_range, end_range)
    
    if not bookings:
        return

    for user_id, start_time_iso, _ in bookings:
        dt = datetime.fromisoformat(start_time_iso)
        time_str = dt.strftime("%H:%M")
        
        text = (
            f"👋 Привет!\n"
            f"⏳ Напоминаем: ваше занятие сегодня в **{time_str}**.\n"
            f"Ждем вас через 2 часа!"
        )
        try:
            await bot.send_message(user_id, text, parse_mode="Markdown")
        except Exception:
            logger.error(f"Не удалось отправить напоминание {user_id}")