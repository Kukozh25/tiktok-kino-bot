import os
import logging
import random
import requests
import csv
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Скрипт автоматически заберет ключи из скрытых настроек Render
API_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_SHEET_ID = os.getenv("SHEET_ID")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

def get_movies_from_sheet():
    url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv"
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'
        lines = response.text.splitlines()
        reader = csv.DictReader(lines)
        return list(reader)
    except Exception as e:
        logging.error(f"Ошибка чтения таблицы: {e}")
        return []

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    btn_random = types.InlineKeyboardButton("🎲 Случайный фильм", callback_data="get_random")
    markup.add(btn_random)
    
    await message.reply(
        "Привет! 🍿 Добро пожаловать в кино-бота.\n\n"
        "Пришли мне **КОД фильма** из TikTok или нажми на кнопку ниже, чтобы выбрать случайное кино на вечер!👇",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@dp.callback_query_handler(lambda c: c.data == 'get_random')
async def process_callback_random(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    movies = get_movies_from_sheet()
    
    if not movies:
        await bot.send_message(callback_query.from_user.id, "❌ Не удалось подключиться к базе данных. Проверьте настройки доступа таблицы.")
        return
        
    movie = random.choice(movies)
    text = (
        f"🎬 **Фильм на вечер:** {movie.get('Название', 'Без названия')}\n"
        f"🎭 **Жанр:** {movie.get('Жанр', '-')}\n\n"
        f"📝 **Описание:** {movie.get('Описание', '-')}\n\n"
        f"🍿 *Полный фильм смотри в нашем официальном канале по ссылке:*\n"
        f"👉 {movie.get('Ссылка', 'Ссылка скоро появится')}"
    )
    await bot.send_message(callback_query.from_user.id, text, parse_mode="Markdown")

@dp.message_handler()
async def search_by_code(message: types.Message):
    user_code = message.text.strip()
    movies = get_movies_from_sheet()
    
    if not movies:
        await bot.reply_to(message, "❌ База данных временно недоступна.")
        return

    found_movie = None
    for movie in movies:
        if movie.get('Код', '').strip() == user_code:
            found_movie = movie
            break
            
    if found_movie:
        text = (
            f"🎬 **Найден фильм по коду {user_code}:**\n\n"
            f"🍿 **Название:** {found_movie.get('Название', 'Без названия')}\n"
            f"🎭 **Жанр:** {found_movie.get('Жанр', '-')}\n\n"
            f"📝 **Описание:** {found_movie.get('Описание', '-')}\n\n"
            f"🍿 *Полный фильм смотри в нашем официальном канале по ссылке:*\n"
            f"👉 {found_movie.get('Ссылка', 'Ссылка скоро появится')}"
        )
        await message.reply(text, parse_mode="Markdown")
    else:
        await message.reply("😔 Фильм с таким кодом не найден. Проверь цифры и попробуй ещё раз!")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
