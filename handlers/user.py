from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import date, datetime

from keyboards import days_keyboard, slots_keyboard, bookings_keyboard
from states import UserRegistration
from db import (
    get_free_slots, book_slot_safe, get_user_bookings, 
    cancel_booking, set_user_name, get_user_name,
    get_slot_time_str, get_slot_time_by_booking
)


router = Router()

START_TEXT = (
    "👋 **Главное меню**\n\n"
    "Доступные команды:\n"
    "/name — Регистрация (Имя и Фамилия)\n"
    "/new — Записаться на занятие\n"
    "/my — Просмотр и редактирование записей\n"
    "/admin — Функции для администратора"
)


async def check_registration(message: Message) -> bool:
    user_id = message.from_user.id
    name = await get_user_name(user_id)
    
    if name:
        return True

    await message.answer(
        "🛑 **Доступ ограничен**\n\n"
        "Сначала укажите свои **Имя и Фамилию**.\n"
        "👉 Введите команду /name",
        parse_mode="Markdown"
    )
    return False


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(START_TEXT, parse_mode="Markdown")


@router.message(Command("name"))
async def cmd_name(message: Message, state: FSMContext):
    await message.answer(
        "📝 **Введите Имя и Фамилию** через пробел:\n"
        "Например: `Иван Иванов`",
        parse_mode="Markdown"
    )
    await state.set_state(UserRegistration.waiting_for_name)


@router.message(UserRegistration.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    
    if len(full_name.split()) < 2:
        return await message.answer("⚠ Введите и имя, и фамилию (минимум два слова):")

    display_name = full_name
    if message.from_user.username:
        display_name += f" (@{message.from_user.username})"

    await set_user_name(message.from_user.id, display_name)
    await state.clear()
    await message.answer(f"✅ Данные сохранены: `{display_name}`")
    await message.answer(START_TEXT, parse_mode="Markdown")


@router.message(Command("new"))
async def new_booking(message: Message):
    if not await check_registration(message): 
        return
    
    slots = await get_free_slots()
    if not slots:
        await message.answer("😔 Свободных окон пока нет.")
        return await message.answer(START_TEXT, parse_mode="Markdown")
    
    unique_days = sorted({datetime.fromisoformat(s[1]).date() for s in slots})
    await message.answer("📅 Выберите дату занятия:", reply_markup=days_keyboard(unique_days, "user_day"))


@router.message(Command("my"))
async def my_bookings(message: Message):
    if not await check_registration(message): 
        return
    
    res = await get_user_bookings(message.from_user.id)
    if not res:
        await message.answer("У вас нет активных записей.")
        await message.answer(START_TEXT, parse_mode="Markdown")
    else:
        await message.answer("📋 Ваши записи:", reply_markup=bookings_keyboard(res))


@router.callback_query(F.data.startswith("user_day:"))
async def user_choose_day(callback: CallbackQuery):
    day_str = callback.data.split(":")[1]
    selected_day = date.fromisoformat(day_str)
    slots = await get_free_slots()
    day_slots = [s for s in slots if datetime.fromisoformat(s[1]).date() == selected_day]
    
    if not day_slots:
        await callback.message.edit_text("😔 К сожалению, на этот день доступных окон нет.")
    else:
        await callback.message.edit_text(
            f"🕒 Свободное время на {selected_day.strftime('%d.%m')}:", 
            reply_markup=slots_keyboard(day_slots)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("slot:"))
async def do_booking(callback: CallbackQuery):
    slot_id = int(callback.data.split(":")[1])
    
    slot_time = await get_slot_time_str(slot_id)

    if await book_slot_safe(callback.from_user.id, slot_id):
        await callback.message.edit_text(f"✅ Вы успешно записаны на **{slot_time}**!", parse_mode="Markdown")
    else:
        await callback.message.edit_text(f"⚠ Время **{slot_time}** уже занято.", parse_mode="Markdown")
    
    await callback.message.answer(START_TEXT, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("cancel:"))
async def user_cancel(callback: CallbackQuery):
    b_id = int(callback.data.split(":")[1])
    
    slot_time = await get_slot_time_by_booking(b_id)
    
    await cancel_booking(b_id)
    await callback.message.edit_text(f"❌ Запись на **{slot_time}** отменена.", parse_mode="Markdown")
    
    await callback.message.answer(START_TEXT, parse_mode="Markdown")
    await callback.answer()