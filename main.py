import datetime
import os
import sqlite3
import time

from dotenv import load_dotenv
from telebot import TeleBot, types
load_dotenv()
bot = TeleBot(os.getenv('BOT_TOKEN'))
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
markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                   one_time_keyboard=False)
markup.add('got up', '30 days avg')


@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, '🌞ㅤ', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'got up')
def handle_got_up_button(message):
    user_id = message.from_user.id
    now = datetime.datetime.now()
    current_time = now.strftime('%H:%M')
    try:
        cursor.execute(
            'INSERT OR REPLACE INTO getup_times (user_id, date, time) VALUES '
            '(?, ?, ?)',
            (user_id, now.strftime('%Y-%m-%d'), current_time))
        conn.commit()
        time.sleep(1)
        bot.send_message(message.chat.id, current_time, reply_markup=markup)
        time.sleep(1)
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        bot.send_message(message.chat.id, str(e), reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == '30 days avg')
def handle_month_abg_button(message):
    user_id = message.from_user.id
    now = datetime.datetime.now()
    thirty_days_ago = (now - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    try:
        cursor.execute('''
        SELECT time FROM getup_times 
        WHERE user_id = ? 
        AND date >= ?
        ''', (user_id, thirty_days_ago))
        time_records = cursor.fetchall()
        total_minutes = sum(
            int(time_record[0].split(':')[0]) * 60 + int(
                time_record[0].split(':')[1]) for time_record in time_records)
        avg_min = total_minutes / len(time_records)
        avg_time = f'{int(avg_min // 60):02d}:{int(avg_min % 60):02d}'
        time.sleep(1)
        bot.send_message(message.chat.id, f'30 days avg {avg_time}',
                         reply_markup=markup)
        time.sleep(1)
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        bot.send_message(message.chat.id, str(e), reply_markup=markup)


@bot.message_handler()
def record_getup_time(message):
    user_id = message.from_user.id
    now = datetime.datetime.now()
    current_date = now.strftime('%Y-%m-%d')
    try:
        time_text = message.text.strip()
        if ':' in time_text:
            hours, minutes = map(int, time_text.split(':'))
        else:
            time_str = time_text.zfill(4)
            hours, minutes = int(time_str[:2]), int(time_str[2:])
        if not (0 <= hours < 24 and 0 <= minutes < 60):
            raise ValueError('incorrect time')
        current_time = f'{hours:02d}:{minutes:02d}'
        cursor.execute(
            'INSERT OR REPLACE INTO getup_times VALUES (?, ?, ?)',
            (user_id, current_date, current_time))
        conn.commit()
        time.sleep(1)
        bot.send_message(message.chat.id, current_time, reply_markup=markup)
        time.sleep(1)
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        bot.send_message(message.chat.id, str(e), reply_markup=markup)


if __name__ == '__main__':
    bot.infinity_polling()
