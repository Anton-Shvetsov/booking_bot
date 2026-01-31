import aiosqlite
from datetime import datetime, timedelta, date
from config import DB_NAME


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY,
            start_time TEXT UNIQUE,
            end_time TEXT,
            is_booked INTEGER DEFAULT 0
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            user_name TEXT, 
            slot_id INTEGER UNIQUE
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT
        )""")
        await db.commit()


async def set_user_name(user_id: int, full_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO users (user_id, full_name) VALUES (?, ?)",
            (user_id, full_name)
        )
        await db.commit()


async def get_user_name(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else None


async def get_slots_on_day(day: date):
    """Возвращает список start_time (ISO string) для конкретного дня."""
    day_str = day.isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT start_time FROM slots WHERE start_time LIKE ?", 
            (f"{day_str}%",)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def add_slots_for_day(start: datetime, end: datetime):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO slots (start_time, end_time) VALUES (?, ?)",
            (start.isoformat(), end.isoformat())
        )
        await db.commit()


async def delete_slot_by_time(start_time: str):
    """Удаляет слот и возвращает user_id, если на слот была запись."""
    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            "SELECT s.id, b.user_id FROM slots s LEFT JOIN bookings b ON s.id = b.slot_id WHERE s.start_time = ?", 
            (start_time,)
        )
        row = await cursor.fetchone()
        
        user_id_to_notify = None
        if row:
            slot_id, user_id = row
            user_id_to_notify = user_id
            
            await db.execute("DELETE FROM bookings WHERE slot_id = ?", (slot_id,))
            await db.execute("DELETE FROM slots WHERE id = ?", (slot_id,))
            await db.commit()
            
        return user_id_to_notify


async def get_slot_time_str(slot_id: int) -> str:
    """Получает строку времени для конкретного слота по его ID."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT start_time FROM slots WHERE id = ?", (slot_id,))
        row = await cursor.fetchone()
        if row:
            dt = datetime.fromisoformat(row[0])
            return dt.strftime("%d.%m в %H:%M")
        return "неизвестное время"


async def get_slot_time_by_booking(booking_id: int) -> str:
    """Получает строку времени для слота, привязанного к записи."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT s.start_time FROM slots s 
            JOIN bookings b ON s.id = b.slot_id 
            WHERE b.id = ?
        """, (booking_id,))
        row = await cursor.fetchone()
        if row:
            dt = datetime.fromisoformat(row[0])
            return dt.strftime("%d.%m в %H:%M")
        return "неизвестное время"


async def get_free_slots():
    """Возвращает только те свободные слоты, время начала которых еще не наступило."""
    async with aiosqlite.connect(DB_NAME) as db:

        now_iso = datetime.now().isoformat()
        
        query = """
            SELECT id, start_time FROM slots 
            WHERE is_booked = 0 AND start_time > ? 
            ORDER BY start_time ASC
        """
        cursor = await db.execute(query, (now_iso,))
        return await cursor.fetchall()


async def book_slot_safe(user_id: int, slot_id: int, user_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM bookings WHERE slot_id = ?", (slot_id,))
        row = await cursor.fetchone()
        
        if row:
            if row[0] == user_id:
                return "already_yours"
            return "taken_by_other"
            
        try:
            await db.execute(
                "INSERT INTO bookings (user_id, slot_id, user_name) VALUES (?, ?, ?)",
                (user_id, slot_id, user_name)
            )
            await db.execute("UPDATE slots SET is_booked = 1 WHERE id = ?", (slot_id,))
            await db.commit()
            return "success"
        except Exception:
            return "error"


async def count_user_bookings(user_id: int) -> int:
    """Возвращает количество будущих записей пользователя."""
    async with aiosqlite.connect(DB_NAME) as db:
        now = datetime.now().isoformat()
        query = "SELECT COUNT(*) FROM bookings b JOIN slots s ON b.slot_id = s.id WHERE b.user_id = ? AND s.start_time > ?"
        cursor = await db.execute(query, (user_id, now))
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_user_bookings(user_id: int):
    """Возвращает список будущих бронирований пользователя."""
    async with aiosqlite.connect(DB_NAME) as db:
        now = datetime.now().isoformat()
        query = """
            SELECT b.id, s.start_time 
            FROM bookings b
            JOIN slots s ON b.slot_id = s.id
            WHERE b.user_id = ? AND s.start_time > ?
            ORDER BY s.start_time ASC
        """
        cursor = await db.execute(query, (user_id, now))
        return await cursor.fetchall()


async def get_booking_start_time(booking_id: int):
    """Возвращает start_time (ISO строку) для конкретной записи."""
    async with aiosqlite.connect(DB_NAME) as db:
        query = """
            SELECT s.start_time 
            FROM bookings b
            JOIN slots s ON b.slot_id = s.id
            WHERE b.id = ?
        """
        cursor = await db.execute(query, (booking_id,))
        row = await cursor.fetchone()
        return row[0] if row else None


async def cancel_booking(booking_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT slot_id FROM bookings WHERE id = ?", (booking_id,))
        res = await cursor.fetchone()
        if res:
            slot_id = res[0]
            await db.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
            await db.execute("UPDATE slots SET is_booked = 0 WHERE id = ?", (slot_id,))
            await db.commit()


async def get_all_bookings_report():
    async with aiosqlite.connect(DB_NAME) as db:
        query = """
            SELECT s.start_time, b.user_name 
            FROM bookings b
            JOIN slots s ON b.slot_id = s.id
            ORDER BY s.start_time ASC
        """
        cursor = await db.execute(query)
        return await cursor.fetchall()
    

async def get_bookings_for_day(target_date: date):
    """Получает все записи на конкретную дату."""
    day_str = target_date.isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        query = """
            SELECT s.start_time, b.user_name 
            FROM bookings b
            JOIN slots s ON b.slot_id = s.id
            WHERE s.start_time LIKE ?
            ORDER BY s.start_time ASC
        """
        cursor = await db.execute(query, (f"{day_str}%",))
        return await cursor.fetchall()


async def get_bookings_in_time_range(start_dt: datetime, end_dt: datetime):
    """
    Ищет записи, у которых start_time попадает в интервал [start_dt, end_dt].
    Возвращает список кортежей (user_id, start_time, full_name).
    """
    start_str = start_dt.isoformat()
    end_str = end_dt.isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        query = """
            SELECT b.user_id, s.start_time, u.full_name
            FROM bookings b
            JOIN slots s ON b.slot_id = s.id
            JOIN users u ON b.user_id = u.user_id
            WHERE s.start_time >= ? AND s.start_time < ?
        """
        cursor = await db.execute(query, (start_str, end_str))
        return await cursor.fetchall()


async def clear_day_data(target_date: date):
    """Удаляет слоты и записи за конкретное число."""
    day_str = target_date.isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            DELETE FROM bookings WHERE slot_id IN (
                SELECT id FROM slots WHERE start_time LIKE ?
            )
        """, (f"{day_str}%",))
        await db.execute(
            "DELETE FROM slots WHERE start_time LIKE ?",
            (f"{day_str}%",))
        await db.commit()


async def clear_all_bookings_and_slots():
    """Полная очистка всех записей и освобождение всех слотов."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM bookings")
        await db.execute("DELETE FROM slots") 
        await db.commit()