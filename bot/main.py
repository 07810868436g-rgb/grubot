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

CHANNEL_RU = "@robuxtap_ru" 
CHANNEL_SNG = "@robuxtap_sng"
WEB_APP_URL = "https://grubot-o9or3ihzw-07810868436g-5373s-projects.vercel.app" # <--- ВСТАВЬ СВОЮ ССЫЛКУ

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Настройка Базы Данных
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    referrer_id INTEGER
                )''')
conn.commit()

async def check_subscription(user_id, channel_username):
    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

# Обновленный /start (теперь бот сразу дает кнопку ИГРАТЬ, если уже подписан)
@dp.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    
    # Обработка рефералов
    ref_id = None
    if command.args and command.args.startswith("ref_"):
        ref_id_str = command.args.split("_")[1]
        if ref_id_str.isdigit() and int(ref_id_str) != user_id:
            ref_id = int(ref_id_str)

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, referrer_id) VALUES (?, ?)", (user_id, ref_id))
        conn.commit()
        if ref_id:
            try:
                await bot.send_message(ref_id, "🎉 Ура! По твоей ссылке зарегистрировался новый друг!")
            except:
                pass

    # Проверяем подписку
    is_sub_ru = await check_subscription(user_id, CHANNEL_RU)
    is_sub_sng = await check_subscription(user_id, CHANNEL_SNG)
    
    if is_sub_ru or is_sub_sng:
        # Считаем друзей и прячем это в ссылку!
        cursor.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,))
        refs_count = cursor.fetchone()[0]
        custom_url = f"{WEB_APP_URL}?refs={refs_count}"
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🎮 Играть в RobuxTap", web_app=WebAppInfo(url=custom_url)))
        await message.answer("С возвращением! 🚀\nЖми кнопку ниже, чтобы запустить игру.", reply_markup=builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🇷🇺 Канал (РФ)", url=f"https://t.me/{CHANNEL_RU[1:]}"))
        builder.row(types.InlineKeyboardButton(text="🌍 Канал (СНГ/Другие)", url=f"https://t.me/{CHANNEL_SNG[1:]}"))
        builder.row(types.InlineKeyboardButton(text="✅ Я подписался (Проверить)", callback_data="check_sub"))
        await message.answer("Привет! Добро пожаловать в RobuxTap 🚀\n\nЧтобы начать играть, подпишись на один из наших каналов.", reply_markup=builder.as_markup())

# Кнопка проверки
@dp.callback_query(F.data == "check_sub")
async def process_check(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    is_sub_ru = await check_subscription(user_id, CHANNEL_RU)
    is_sub_sng = await check_subscription(user_id, CHANNEL_SNG)
    
    if is_sub_ru or is_sub_sng:
        # Точно так же считаем друзей и прячем в ссылку
        cursor.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,))
        refs_count = cursor.fetchone()[0]
        custom_url = f"{WEB_APP_URL}?refs={refs_count}"
        
        game_builder = InlineKeyboardBuilder()
        game_builder.row(types.InlineKeyboardButton(text="🎮 Играть в RobuxTap", web_app=WebAppInfo(url=custom_url)))
        await callback.message.edit_text("🎉 Отлично! Подписка подтверждена.\n\nЖми кнопку ниже, чтобы запустить игру!", reply_markup=game_builder.as_markup())
    else:
        await callback.answer("❌ Ты еще не подписался!", show_alert=True)

async def main():
    print("Бот успешно обновлен и запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())