import asyncio
import datetime
import os
import sqlite3

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv
load_dotenv()

bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher()

conn = sqlite3.connect('getup_times.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS getup_times (
    user_id INTEGER,
    date TEXT,
    time TEXT,
    PRIMARY KEY (user_id, date)
)
''')
conn.commit()


def get_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text='got up'),
                KeyboardButton(text='this_month avg'))
    return builder.as_markup(resize_keyboard=True)


keyboard = get_keyboard()


@dp.message(Command('start'))
async def handle_start(message: types.Message):
    await message.answer(':*', reply_markup=keyboard)


@dp.message(F.text == 'got up')
async def record_wakeup_time(message: types.Message):
    user_id = message.from_user.id
    now = datetime.datetime.now()
    current_date = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M')

    try:
        cursor.execute(
            'INSERT OR REPLACE INTO getup_times (user_id, date, '
            'time) VALUES (?, ?, ?)',
            (user_id, current_date, current_time))
        conn.commit()
        await message.answer(current_time, reply_markup=keyboard)
        await asyncio.sleep(1)
        await message.delete()
    except Exception as e:
        await message.answer(str(e))


@dp.message(F.text == 'this_month avg')
async def show_this_month_average(message: types.Message):
    user_id = message.from_user.id
    now = datetime.datetime.now()
    current_month = now.month
    current_year = now.year

    try:
        cursor.execute('''
        SELECT time FROM getup_times 
        WHERE user_id = ? 
        AND strftime('%m', date) = ? 
        AND strftime('%Y', date) = ?
        ''', (user_id, f'{current_month:02d}', str(current_year)))

        times_records = cursor.fetchall()
        if not times_records:
            answer = await message.answer(
                'there are no getups in this month yet')
            await asyncio.sleep(3)
            await message.delete()
            await bot.delete_message(chat_id=answer.chat.id,
                                     message_id=answer.message_id)
            return

        total_minutes = 0
        count = 0
        for time_record in times_records:
            hours, minutes = map(int, time_record[0].split(':'))
            total_minutes += hours * 60 + minutes
            count += 1

        average_minutes = total_minutes / count
        avg_hours = int(average_minutes // 60)
        avg_minutes = int(average_minutes % 60)

        await message.answer(
            f'this_month avg: {avg_hours:02d}:{avg_minutes:02d}')
        await asyncio.sleep(1)
        await message.delete()
    except Exception as e:
        await message.answer(str(e))


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
