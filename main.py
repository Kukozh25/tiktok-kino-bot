import os
import logging
import random
import requests
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web

API_TOKEN = os.getenv("BOT_TOKEN")
SCRIPT_URL = os.getenv("SCRIPT_URL")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

def get_movies_from_sheet():
    try:
        response = requests.get(SCRIPT_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        logging.error(f"Ошибка получения данных через веб-приложение: {e}")
        return []

def format_rating(rating_val):
    try:
        return f"{float(rating_val):.1f}"
    except:
        return str(rating_val) if rating_val else "-"

@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="🎲 Случайный фильм", callback_data="get_random"))
    
    await message.reply(
        "Привет! 🍿 Добро пожаловать в кино-бота.\n\n"
        "Пришли мне **КОД фильма** из TikTok или нажми на кнопку ниже, чтобы выбрать случайное кино на вечер!👇",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@dp.callback_query_handler(lambda c: c.data == 'get_random')
async def process_callback_random(callback_query: types.CallbackQuery):
    await callback_query.answer()
    movies = get_movies_from_sheet()
    
    if not movies:
        await bot.send_message(callback_query.from_user.id, "❌ База данных временно недоступна. Попробуйте позже.")
        return
        
    movie = random.choice(movies)
    link = movie.get('link to post', '').strip() if movie.get('link to post') else ""
    if not link:
        link = "Ссылка скоро появится в нашем канале!"
        
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

@dp.message_handler()
async def search_by_code(message: types.Message):
    user_code = message.text.strip()
    if not user_code.isdigit():
        return

    movies = get_movies_from_sheet()
    if not movies:
        await message.reply("❌ База данных временно недоступна.")
        return

    found_movie = None
    for movie in movies:
        raw_code = str(movie.get('code from tt', '')).strip()
        
        if '.' in raw_code:
            sheet_code = raw_code.split('.')[0]
        else:
            sheet_code = raw_code
        
        if sheet_code == user_code:
            found_movie = movie
            break
            
    if found_movie:
        link = found_movie.get('link to post', '').strip() if found_movie.get('link to post') else ""
        if not link:
            link = "Ссылка скоро появится в нашем канале!"
            
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
        await message.reply("😔 Фильм с таким кодом не найден. Проверь цифры!")

# Маленький фоновый веб-сервер, чтобы Render не ругался на порты
async def handle_hc(request):
    return web.Response(text="Bot is perfectly alive")

async def start_background_server():
    app = web.Application()
    app.router.add_get('/', handle_hc)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

if __name__ == '__main__':
    # Запускаем фоновый веб-сервер для проверки портов Render
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_background_server())
    
    # Сбрасываем возможные старые зависшие вебхуки в Telegram перед стартом поллинга
    loop.run_until_complete(bot.delete_webhook())
    
    # Запускаем стандартный опрос
    executor.start_polling(dp, skip_updates=True)
