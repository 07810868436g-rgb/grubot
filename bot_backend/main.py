import asyncio
import os
import sqlite3
import time
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command, CommandStart, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- ТВОИ НАСТРОЙКИ ---
YOUR_TELEGRAM_ID = 8685355990  # <--- ТВОЙ ID
CHANNEL_RU = "@robuxtap_ru" 
CHANNEL_SNG = "@robuxtap_sng"
WEB_APP_URL = "https://grubot-30lh32dr0-07810868436g-5373s-projects.vercel.app" # <--- ТВОЯ ССЫЛКА НА ИГРУ

# --- НАСТРОЙКИ БАННЕРОВ (ССЫЛКИ НА КАРТИНКИ) ---
BANNER_WELCOME = "https://images.unsplash.com/photo-1614680376573-df3480f0c6ff?q=80&w=1000&auto=format&fit=crop" # Картинка для проверки подписки
BANNER_GAME = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1000&auto=format&fit=crop"    # Картинка для кнопки "Играть"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- БАЗА ДАННЫХ ---
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
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        return False

# --- ПРИЕМ ЗАЯВКИ НА ВЫВОД ИЗ МИНИ-АППА ---
@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        
        if data.get("action") == "withdraw":
            amount = data.get("amount")
            roblox_nick = data.get("nickname")
            user = message.from_user
            
            await message.answer(
                f"✅ <b>Заявка на вывод успешно создана!</b>\n\n"
                f"💰 <b>Сумма:</b> {amount} R$\n"
                f"🎮 <b>Ник в Roblox:</b> {roblox_nick}\n\n"
                f"⏳ Администрация проверит и зачислит робуксы в течение 24 часов. "
                f"Убедись, что у тебя создан геймпас на эту сумму!",
                parse_mode="HTML"
            )
            
            admin_text = (
                f"🚨 <b>НОВАЯ ЗАЯВКА НА ВЫВОД ROBUX!</b>\n\n"
                f"👤 <b>Игрок:</b> {user.first_name} \n"
                f"🆔 <b>ID Телеграм:</b> <code>{user.id}</code>\n"
                f"📱 <b>Юзернейм:</b> @{user.username if user.username else 'нету'}\n"
                f"💰 <b>Сумма к выводу:</b> {amount} R$\n"
                f"🎮 <b>Ник в Roblox:</b> <code>{roblox_nick}</code>\n\n"
                f"ℹ️ Переведи робуксы игроку и напиши ему в личку об успешной выплате."
            )
            await bot.send_message(chat_id=YOUR_TELEGRAM_ID, text=admin_text, parse_mode="HTML")
            
    except Exception as e:
        print(f"Ошибка при обработке вывода: {e}")

@dp.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    # Обработка реферальной системы
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
                await bot.send_message(ref_id, "🎉 <b>Ура! По твоей ссылке зарегистрировался новый друг!</b>", parse_mode="HTML")
            except: 
                pass

    is_sub_ru = await check_subscription(user_id, CHANNEL_RU)
    is_sub_sng = await check_subscription(user_id, CHANNEL_SNG)
    
    if is_sub_ru or is_sub_sng:
        cursor.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,))
        refs_count = cursor.fetchone()[0]
        current_time = int(time.time())
        
        # ДИНАМИЧЕСКАЯ ССЫЛКА ДЛЯ СБРОСА КЕША
        custom_url = f"{WEB_APP_URL}?refs={refs_count}&v={current_time}"
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🎮 ИГРАТЬ (Tap to Earn)", web_app=WebAppInfo(url=custom_url)))
        
        text = (
            f"🚀 <b>С возвращением, {first_name}!</b>\n\n"
            f"Твоя империя ждет тебя. Залетай в игру, собирай поинты, "
            f"используй секретные бусты и выводи реальные робуксы! 💸\n\n"
            f"👇 <b>Жми на кнопку ниже, чтобы войти в игру:</b>"
        )
        await message.answer_photo(photo=BANNER_GAME, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🇷🇺 Канал (РФ)", url=f"https://t.me/{CHANNEL_RU[1:]}"))
        builder.row(types.InlineKeyboardButton(text="🌍 Канал (СНГ/Другие)", url=f"https://t.me/{CHANNEL_SNG[1:]}"))
        builder.row(types.InlineKeyboardButton(text="✅ Я подписался (Проверить)", callback_data="check_sub"))
        
        text = (
            f"👋 <b>Привет, {first_name}! Добро пожаловать в RobuxTap!</b> 💎\n\n"
            f"Здесь ты можешь бесплатно добывать Робуксы, просто тапая по экрану "
            f"и выполняя легкие задания.\n\n"
            f"🔒 <b>Внимание:</b> Для доступа к игре необходимо подписаться на один из наших "
            f"официальных каналов. Выбери свой регион ниже:"
        )
        await message.answer_photo(photo=BANNER_WELCOME, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "check_sub")
async def process_check(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    first_name = callback.from_user.first_name
    is_sub_ru = await check_subscription(user_id, CHANNEL_RU)
    is_sub_sng = await check_subscription(user_id, CHANNEL_SNG)
    
    if is_sub_ru or is_sub_sng:
        cursor.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,))
        refs_count = cursor.fetchone()[0]
        current_time = int(time.time())
        
        # ДИНАМИЧЕСКАЯ ССЫЛКА ДЛЯ СБРОСА КЕША
        custom_url = f"{WEB_APP_URL}?refs={refs_count}&v={current_time}"
        
        game_builder = InlineKeyboardBuilder()
        game_builder.row(types.InlineKeyboardButton(text="🎮 ИГРАТЬ (Tap to Earn)", web_app=WebAppInfo(url=custom_url)))
        
        text = (
            f"✅ <b>Отлично, {first_name}! Подписка подтверждена.</b>\n\n"
            f"Теперь тебе доступен весь функционал RobuxTap. Запускай игру "
            f"и начни зарабатывать прямо сейчас! 🎮"
        )
        
        await callback.message.delete()
        await bot.send_photo(chat_id=callback.message.chat.id, photo=BANNER_GAME, caption=text, reply_markup=game_builder.as_markup(), parse_mode="HTML")
    else:
        await callback.answer("❌ Ты еще не подписался! Проверь подписку и нажми кнопку снова.", show_alert=True)

async def main():
    print("Бот запущен. Баннеры и кеш-бастер работают!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())