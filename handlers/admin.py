from aiogram import Bot
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from datetime import date, timedelta, time, datetime
from logger_config import logger
import contextlib

from filters import IsAdmin
from keyboards import days_keyboard, slots_tickbox
from db import (add_slots_for_day, get_slots_on_day,
                delete_slot_by_time, get_all_bookings_report,
                clear_all_bookings_and_slots, set_max_user_bookings)
from states import AdminAddSlots

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

ADMIN_MENU = (
    "👑 **Админ-панель**\n\n"
    "/editslots — Управление расписанием (добавить/удалить слоты)\n\n"
    "/setmaxbookings <n> — Установка лимита записей для одного пользователя\n\n"
    "/all — Просмотреть все записи пользователей"
)


def get_admin_time_slots():
    return [time(hour=h, minute=30) for h in range(11, 22)]


def escape_md(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)


@router.message(Command("admin"))
async def admin_panel(message: Message):
    await message.answer(ADMIN_MENU, parse_mode="Markdown")


@router.message(Command("editslots"))
async def add_slots_start(message: Message, state: FSMContext):
    today = date.today()
    days = [today + timedelta(days=i) for i in range(7)]
    await state.set_state(AdminAddSlots.choosing_day)
    await message.answer("📅 Выберите день:", reply_markup=days_keyboard(days, "admin_day"))


@router.callback_query(AdminAddSlots.choosing_day, F.data.startswith("admin_day:"))
async def admin_choose_day(callback: CallbackQuery, state: FSMContext):
    day_str = callback.data.split(":", 1)[1]
    day_date = date.fromisoformat(day_str)

    existing_slots_iso = await get_slots_on_day(day_date)
    
    selected = set()
    for iso_str in existing_slots_iso:
        dt = datetime.fromisoformat(iso_str)
        selected.add(dt.strftime("%H:%M"))

    await state.update_data(day=day_str, selected=selected)
    await state.set_state(AdminAddSlots.choosing_slots)
    
    slots = get_admin_time_slots()
    
    await callback.message.edit_text(
        f"🕒 Редактирование {day_str}.\nСнимите галочку, чтобы удалить слот (и запись!):", 
        reply_markup=slots_tickbox(slots, selected)
    )
    await callback.answer()


@router.callback_query(AdminAddSlots.choosing_slots, F.data.startswith("toggle:"))
async def toggle_slot(callback: CallbackQuery, state: FSMContext):
    t_str = callback.data.split(":", 1)[1]
    data = await state.get_data()
    selected = data.get("selected", set())

    if t_str in selected:
        selected.remove(t_str)
    else:
        selected.add(t_str)

    await state.update_data(selected=selected)
    slots = get_admin_time_slots()
    
    with contextlib.suppress(TelegramBadRequest):
        await callback.message.edit_reply_markup(
            reply_markup=slots_tickbox(slots, selected)
        )
    await callback.answer()


@router.callback_query(AdminAddSlots.choosing_slots, F.data == "confirm_slots")
async def confirm_slots(callback: CallbackQuery, state: FSMContext, bot: Bot):
    admin_id = callback.from_user.id
    data = await state.get_data()
    selected_set = data.get("selected", set())
    day_str = data.get("day")
    day = date.fromisoformat(day_str)

    existing_slots_iso = await get_slots_on_day(day)
    existing_set = {datetime.fromisoformat(iso).strftime("%H:%M") for iso in existing_slots_iso}

    to_add = selected_set - existing_set
    to_delete = existing_set - selected_set

    added, deleted, notified = 0, 0, 0

    for t_str in to_add:
        t = datetime.strptime(t_str, "%H:%M").time()
        start = datetime.combine(day, t)
        await add_slots_for_day(start, start + timedelta(hours=1))
        added += 1

    for t_str in to_delete:
        t = datetime.strptime(t_str, "%H:%M").time()
        start_dt = datetime.combine(day, t)
        user_id = await delete_slot_by_time(start_dt.isoformat())
        deleted += 1
        if user_id:
            logger.info(f"ОТМЕНА: (АДМИН) Пользователь {user_id} на {start_dt.strftime('%d.%m в %H:%M')}")
            try:
                await bot.send_message(
                    user_id, 
                    f"⚠️ Ваша запись на **{start_dt.strftime('%d.%m в %H:%M')}** была отменена администратором.",
                    parse_mode="Markdown"
                )
                notified += 1
            except Exception: pass

    await state.clear()
    
    result_text = (
        f"✅ **Изменения сохранены для {day_str}**\n"
        f"➕ Добавлено: {added}\n"
        f"➖ Удалено: {deleted}\n"
        f"🔔 Уведомлено пользователей: {notified}"
    )
    logger.info(f"АДМИН ({admin_id}): Изменены слоты на {day_str} (добавлено {added}, удалено {deleted})")

    await callback.message.edit_text(result_text, parse_mode="Markdown")
    await callback.message.answer(ADMIN_MENU, parse_mode="Markdown")
    await callback.answer()


@router.message(Command("all"))
async def show_all_bookings(message: Message):
    bookings = await get_all_bookings_report()
    if not bookings:
        await message.answer("📭 Записей пока нет.")
    else:
        report = "📋 **Список всех записей:**\n"
        current_day = ""
        for start_time_iso, user_info in bookings:
            dt = datetime.fromisoformat(start_time_iso)
            day_str = dt.strftime("%d.%m (%a)")
            if day_str != current_day:
                report += f"\n📅 {day_str}\n"
                current_day = day_str
            user_info = escape_md(user_info)
            report += f"  • {dt.strftime('%H:%M')} — {user_info}\n"
        await message.answer(report, parse_mode="Markdown")
    await message.answer(ADMIN_MENU, parse_mode="Markdown")


@router.message(Command("setmaxbookings"))
async def cmd_set_max_bookings(message: Message):
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /setmaxbookings <число>")
        return await message.answer(ADMIN_MENU, parse_mode="Markdown")
    value = int(parts[1])
    await set_max_user_bookings(value)
    await message.answer(
        f"✅ Максимальное число активных записей установлено: **{value}**",
        parse_mode="Markdown"
    )
    await message.answer(ADMIN_MENU, parse_mode="Markdown")


@router.message(Command("forceclearall"))
async def cmd_clear_all(message: Message):
    await clear_all_bookings_and_slots()
    await message.answer(
        "🗑 **Все записи аннулированы.**\n"
        "Таблица бронирований очищена, все слоты снова свободны.",
        parse_mode="Markdown"
    )
    await message.answer(ADMIN_MENU, parse_mode="Markdown")