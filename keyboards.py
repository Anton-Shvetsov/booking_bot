from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date, time, datetime


def days_keyboard(days: list[date], prefix: str) -> InlineKeyboardMarkup:
    buttons = []
    for d in days:
        buttons.append([InlineKeyboardButton(
            text=d.strftime("%d.%m (%a)"),
            callback_data=f"{prefix}:{d.isoformat()}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def slots_keyboard(slots: list) -> InlineKeyboardMarkup:
    buttons = []
    for slot in slots:
        s_id = slot[0]
        start_dt = datetime.fromisoformat(slot[1])
        buttons.append([InlineKeyboardButton(
            text=start_dt.strftime("%H:%M"),
            callback_data=f"slot:{s_id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def bookings_keyboard(bookings: list) -> InlineKeyboardMarkup:
    buttons = []
    for b in bookings:
        b_id = b[0]
        start_dt = datetime.fromisoformat(b[1])
        buttons.append([InlineKeyboardButton(
            text=f"❌ {start_dt.strftime('%d.%m %H:%M')}",
            callback_data=f"cancel:{b_id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def slots_tickbox(all_times: list[time], selected: set[str]) -> InlineKeyboardMarkup:
    buttons = []
    for t in all_times:
        t_str = t.strftime("%H:%M")
        
        mark = "✅ " if t_str in selected else ""
        
        buttons.append([InlineKeyboardButton(
            text=f"{mark}{t_str}",
            callback_data=f"toggle:{t_str}" 
        )])
    
    buttons.append([InlineKeyboardButton(
        text="✔ ПОДТВЕРДИТЬ",
        callback_data="confirm_slots"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)