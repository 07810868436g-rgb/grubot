import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo
from dotenv import load_dotenv

# Открываем "сейф"
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Сюда впиши юзернеймы твоих каналов (с собачкой @ в начале)
CHANNEL_RU = "@robuxtap_ru" 
CHANNEL_SNG = "@robuxtap_sng"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Вспомогательная функция: она "спрашивает" у Телеграма, есть ли человек в канале
async def check_subscription(user_id, channel_username):
    try:
        # Бот проверяет статус пользователя в канале
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        # Если статус "участник", "создатель" или "админ", значит подписан
        return member.status in ["member", "creator", "administrator"]
    except:
        # Если произошла ошибка (например, бот не админ в канале), возвращаем False
        return False

# 1. Реакция на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки-ссылки на каналы
    builder.row(types.InlineKeyboardButton(text="🇷🇺 Канал (РФ)", url=f"https://t.me/{CHANNEL_RU[1:]}"))
    builder.row(types.InlineKeyboardButton(text="🌍 Канал (НЕ РФ)", url=f"https://t.me/{CHANNEL_SNG[1:]}"))
    
    # Добавляем кнопку ПРОВЕРКИ. Обрати внимание на callback_data!
    # Это скрытый сигнал "check_sub", который кнопка отправит боту при нажатии
    builder.row(types.InlineKeyboardButton(text="✅ Я подписался (Проверить)", callback_data="check_sub"))
    
    await message.answer(
        "Привет! Добро пожаловать в RobuxTap 🚀\n\n"
        "Чтобы начать играть и копить робуксы, подпишись на один из наших новостных каналов, а затем нажми кнопку проверки.",
        reply_markup=builder.as_markup()
    )

# 2. Реакция на нажатие кнопки "Проверить" (ловитель скрытого сигнала check_sub)
@dp.callback_query(F.data == "check_sub")
async def process_check(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # Проверяем оба канала
    is_sub_ru = await check_subscription(user_id, CHANNEL_RU)
    is_sub_sng = await check_subscription(user_id, CHANNEL_SNG)
    
    # Если подписан ХОТЯ БЫ НА ОДИН из них (или на оба)
    if is_sub_ru or is_sub_sng:
        # Создаем кнопку для входа в игру
        game_builder = InlineKeyboardBuilder()
        game_builder.row(types.InlineKeyboardButton(
            text="🎮 Играть в RobuxTap",
            web_app=WebAppInfo(url="https://telegram.org") # Пока заглушка
        ))
        
        # Меняем старое сообщение на успешное
        await callback.message.edit_text(
            "🎉 Отлично! Подписка подтверждена.\n\nЖми кнопку ниже, чтобы запустить игру!",
            reply_markup=game_builder.as_markup()
        )
    else:
        # Если не подписан, выдаем всплывающую подсказку
        await callback.answer(
            "❌ Ты еще не подписался! Выбери канал, подпишись и попробуй снова.", 
            show_alert=True
        )

# Запуск бота
async def main():
    print("Бот RobuxTap успешно запущен и готов к проверке подписок!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())