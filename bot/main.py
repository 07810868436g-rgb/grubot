import asyncio
import os
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command, CommandStart, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo
from dotenv import load_dotenv

# Открываем сейф
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ТВОИ НАСТРОЙКИ (проверь, чтобы тут были твои ссылки!)
CHANNEL_RU = "@robuxtap_ru" 
CHANNEL_SNG = "@robuxtap_sng"
WEB_APP_URL = "https://grubot.vercel.app" # <--- ВСТАВЬ СВОЮ ССЫЛКУ

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- 1. НАСТРОЙКА БАЗЫ ДАННЫХ ---
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
# Создаем таблицу, если ее нет. Она хранит ID игрока и ID того, кто его пригласил
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    referrer_id INTEGER
                )''')
conn.commit()

# Функция проверки подписки
async def check_subscription(user_id, channel_username):
    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

# --- 2. ОБНОВЛЕННАЯ КОМАНДА /START ---
# Обрати внимание: мы добавили CommandObject, чтобы бот умел читать параметры после /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    
    # Пытаемся понять, есть ли в ссылке реферальный код
    ref_id = None
    if command.args and command.args.startswith("ref_"):
        ref_id_str = command.args.split("_")[1]
        # Проверяем, что ID состоит из цифр и человек не пригласил сам себя
        if ref_id_str.isdigit() and int(ref_id_str) != user_id:
            ref_id = int(ref_id_str)

    # Ищем пользователя в базе
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        # Если это совершенно новый игрок — добавляем его в базу
        cursor.execute("INSERT INTO users (user_id, referrer_id) VALUES (?, ?)", (user_id, ref_id))
        conn.commit()
        
        # Если он пришел по ссылке друга, отправляем другу уведомление!
        if ref_id:
            try:
                await bot.send_message(
                    chat_id=ref_id, 
                    text="🎉 Ура! По твоей ссылке зарегистрировался новый друг!"
                )
            except Exception:
                pass # Игнорируем ошибку, если друг заблокировал бота

    # Стандартная выдача кнопок с каналами
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🇷🇺 Канал (РФ)", url=f"https://t.me/{CHANNEL_RU[1:]}"))
    builder.row(types.InlineKeyboardButton(text="🌍 Канал (СНГ/Другие)", url=f"https://t.me/{CHANNEL_SNG[1:]}"))
    builder.row(types.InlineKeyboardButton(text="✅ Я подписался (Проверить)", callback_data="check_sub"))
    
    await message.answer(
        "Привет! Добро пожаловать в RobuxTap 🚀\n\n"
        "Чтобы начать играть, подпишись на один из наших каналов.",
        reply_markup=builder.as_markup()
    )

# --- 3. ПРОВЕРКА ПОДПИСКИ (как и было раньше) ---
@dp.callback_query(F.data == "check_sub")
async def process_check(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    is_sub_ru = await check_subscription(user_id, CHANNEL_RU)
    is_sub_sng = await check_subscription(user_id, CHANNEL_SNG)
    
    if is_sub_ru or is_sub_sng:
        game_builder = InlineKeyboardBuilder()
        game_builder.row(types.InlineKeyboardButton(
            text="🎮 Играть в RobuxTap",
            web_app=WebAppInfo(url=WEB_APP_URL)
        ))
        await callback.message.edit_text(
            "🎉 Отлично! Подписка подтверждена.\n\nЖми кнопку ниже, чтобы запустить игру!",
            reply_markup=game_builder.as_markup()
        )
    else:
        await callback.answer("❌ Ты еще не подписался!", show_alert=True)

async def main():
    print("Бот RobuxTap с Базой Данных успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())