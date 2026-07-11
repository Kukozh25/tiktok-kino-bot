import os
import logging
import random
import requests
import csv
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# Ключи из настроек Render
API_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_SHEET_ID = os.getenv("SHEET_ID")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def get_movies_from_sheet():
    url = f"https://google.com{GOOGLE_SHEET_ID}/export?format=csv"
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'
        lines = response.text.splitlines()
        reader = csv.DictReader(lines)
        return list(reader)
    except Exception as e:
        logging.error(f"Ошибка чтения таблицы: {e}")
        return []

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎲 Случайный фильм", callback_data="get_random"))
    
    await message.reply(
        "Привет! 🍿 Добро пожаловать в кино-бота.\n\n"
        "Пришли мне **КОД фильма** из TikTok или нажми на кнопку ниже, чтобы выбрать случайное кино на вечер!👇",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == 'get_random')
async def process_callback_random(callback_query: types.CallbackQuery):
    await callback_query.answer()
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

@dp.message(lambda message: message.text and message.text.strip().isdigit())
async def search_by_code(message: types.Message):
    user_code = message.text.strip()
    movies = get_movies_from_sheet()
    
    if not movies:
        await message.reply("❌ База данных временно недоступна.")
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

# Заглушка для Render, чтобы он думал, что это сайт
async def handle_hc(request):
    return web.Response(text="Bot is running")

async def main():
    # Запуск заглушки порта
    app = web.Application()
    app.router.add_get('/', handle_hc)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    asyncio.create_task(site.start())
    
    # Запуск самого бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

