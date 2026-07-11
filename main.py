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

API_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_SHEET_ID = os.getenv("SHEET_ID")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def get_movies_from_sheet():
    url = f"https://google.com{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        lines = response.text.splitlines()
        reader = csv.DictReader(lines)
        return list(reader)
    except Exception as e:
        logging.error(f"Ошибка чтения таблицы: {e}")
        return []

def format_rating(rating_str):
    try:
        # Округляем рейтинг до 1 знака после запятой
        return f"{float(rating_str):.1f}"
    except:
        return rating_str if rating_str else "-"

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
    
    # Берем ссылку. Если она пустая — пишем стандартный текст со ссылкой на канал
    link = movie.get('link to post', '').strip()
    if not link:
        link = "Ссылка на фильм появится скоро в нашем канале! Подписывайся: https://t.me"
        
    rating = format_rating(movie.get('rating_ball', '-'))
    
    text = (
        f"🎬 **Фильм на вечер:** {movie.get('movie', 'Без названия')}\n"
        f"📅 **Год выпуска:** {movie.get('year', '-')}\n"
        f"⭐️ **Рейтинг:** {rating}\n\n"
        f"📝 **Описание:** {movie.get('overview', '-')}\n\n"
        f"🍿 *Смотреть фильм по ссылке:*\n"
        f"👉 {link}"
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
        if movie.get('code from tt', '').strip() == user_code:
            found_movie = movie
            break
            
    if found_movie:
        link = found_movie.get('link to post', '').strip()
        if not link:
            link = "Ссылка на фильм появится скоро в нашем канале! Подписывайся: https://t.me"
            
        rating = format_rating(found_movie.get('rating_ball', '-'))
        
        text = (
            f"🎬 **Найден фильм по коду {user_code}:**\n\n"
            f"🍿 **Название:** {found_movie.get('movie', 'Без названия')}\n"
            f"📅 **Год выпуска:** {found_movie.get('year', '-')}\n"
            f"⭐️ **Рейтинг:** {rating}\n\n"
            f"📝 **Описание:** {found_movie.get('overview', '-')}\n\n"
            f"🍿 *Смотреть фильм по ссылке:*\n"
            f"👉 {link}"
        )
        await message.reply(text, parse_mode="Markdown")
    else:
        await message.reply("😔 Фильм с таким кодом не найден. Возможно, админ ещё не добавил этот код в таблицу. Проверь цифры!")

async def handle_hc(request):
    return web.Response(text="Bot is running")

async def main():
    app = web.Application()
    app.router.add_get('/', handle_hc)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    asyncio.create_task(site.start())
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

