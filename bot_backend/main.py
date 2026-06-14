import asyncio
import os
import sqlite3
import time
import json
import hashlib
import hmac
from urllib.parse import parse_qsl
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command, CommandStart, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo, LabeledPrice, PreCheckoutQuery
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ==========================================
# ⚠️ БЛОК ДЛЯ ТВОИХ ДАННЫХ (ЗАПОЛНИ ЭТИ СТРОКИ)
# ==========================================
YOUR_TELEGRAM_ID = 8685355990  # Твой ID (для уведомлений о выводе)
CHANNEL_RU = "@robuxtap_ru"    # Твой основной канал
CHANNEL_SNG = "@robuxtap_sng"  # Твой второй канал
WEB_APP_URL = "https://grubot.vercel.app/"  # Ссылка на твой фронтенд (Mini App) в Vercel

# --- НАСТРОЙКИ БАННЕРОВ (ССЫЛКИ НА КАРТИНКИ) ---
BANNER_WELCOME = "https://images.unsplash.com/photo-1614680376573-df3480f0c6ff?q=80&w=1000&auto=format&fit=crop"
BANNER_GAME = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1000&auto=format&fit=crop"    

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==========================================
# БАЗА ДАННЫХ
# ==========================================
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    referrer_id INTEGER,
                    taps_balance INTEGER DEFAULT 0,
                    bonus_balance INTEGER DEFAULT 0,
                    multitap_level INTEGER DEFAULT 1,
                    bot_level INTEGER DEFAULT 0,
                    last_sync_time REAL DEFAULT 0
                )''')
conn.commit()

# ==========================================
# СИСТЕМА БЕЗОПАСНОСТИ (ТАМОЖНЯ)
# ==========================================
def validate_telegram_data(init_data: str, bot_token: str):
    """Расшифровывает и проверяет подпись Telegram."""
    try:
        parsed_data = dict(parse_qsl(init_data))
        received_hash = parsed_data.pop('hash', None)
        if not received_hash:
            return None

        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calculated_hash == received_hash:
            user_data = json.loads(parsed_data.get('user', '{}'))
            return user_data
        
        return None
    except Exception as e:
        print(f"Ошибка валидации: {e}")
        return None

# ==========================================
# HTTP API ДЛЯ МИНИ-АППА
# ==========================================
async def sync_api(request):
    """Принимает клики, считает пассивный доход и офлайн-бота"""
    try:
        data = await request.json()
        init_data = data.get("initData")
        clicks_claimed = data.get("clicks", 0)
        elapsed_time_ms = data.get("elapsed_time_ms", 3000)
        
        # Студийный доход берем с клиента (в будущем лучше брать из БД)
        studio_income_per_sec = data.get("studioIncome", 0) 
        
        user_data = validate_telegram_data(init_data, BOT_TOKEN)
        if not user_data:
            return web.json_response({"error": "Unauthorized"}, status=401)
            
        user_id = user_data.get("id")
        current_time = time.time()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_db = cursor.fetchone()
        
        if not user_db:
             return web.json_response({"error": "User not found in DB"}, status=404)
        
        # Разбираем данные
        taps_balance = user_db[2]
        bonus_balance = user_db[3]
        multitap_level = user_db[4]
        bot_level = user_db[5]
        last_sync_time = user_db[6]
        
        # --- 1. АНТИЧИТ И КЛИКИ ---
        MAX_CLICKS_PER_SEC = 15
        elapsed_sec = elapsed_time_ms / 1000.0 if elapsed_time_ms > 0 else 3.0
        max_possible_clicks = int(MAX_CLICKS_PER_SEC * elapsed_sec)
        valid_clicks = min(clicks_claimed, max_possible_clicks)
        
        earned_from_taps = valid_clicks * multitap_level
        new_taps_balance = taps_balance + earned_from_taps
        
        # --- 2. ПАССИВНЫЙ ДОХОД И ОФЛАЙН-БОТ ---
        earned_passive = 0
        is_offline_reward = False
        
        if last_sync_time > 0:
            time_away_sec = current_time - last_sync_time
            
            if time_away_sec < 60:
                # Игрок онлайн (отправляет запросы каждые 3 секунды)
                earned_passive = int(time_away_sec * studio_income_per_sec)
            else:
                # Игрок был офлайн долгое время
                if bot_level > 0:
                    # Бот работает максимум 3 часа (10800 секунд)
                    active_offline_sec = min(time_away_sec, 10800)
                    earned_passive = int(active_offline_sec * (studio_income_per_sec + bot_level))
                    is_offline_reward = True
        
        new_bonus_balance = bonus_balance + earned_passive
        
        # --- 3. СОХРАНЕНИЕ ---
        cursor.execute('''UPDATE users 
                          SET taps_balance = ?, bonus_balance = ?, last_sync_time = ? 
                          WHERE user_id = ?''', 
                       (new_taps_balance, new_bonus_balance, current_time, user_id))
        conn.commit()
        
        return web.json_response({
            "status": "success", 
            "new_taps_balance": new_taps_balance,
            "new_bonus_balance": new_bonus_balance,
            "earned_offline": earned_passive if is_offline_reward else 0
        })

    except Exception as e:
        print(f"Ошибка в /sync: {e}")
        return web.json_response({"error": "Server error"}, status=500)

async def create_invoice_api(request):
    """Генерирует ссылку для оплаты скинов через Telegram Stars"""
    try:
        prices = [LabeledPrice(label="Нейро-Скин", amount=50)]
        invoice_link = await bot.create_invoice_link(
            title="✨ Генерация ИИ-Скина",
            description="Оплата создания уникального скина в Нейро-кузнице",
            payload="skin_generation_50",
            provider_token="", # ОБЯЗАТЕЛЬНО ПУСТОЙ для Telegram Stars!
            currency="XTR",
            prices=prices
        )
        return web.json_response({"invoice_url": invoice_link})
    except Exception as e:
        print(f"Ошибка создания инвойса: {e}")
        return web.json_response({"error": str(e)}, status=500)

# ==========================================
# ОБРАБОТЧИКИ ПЛАТЕЖЕЙ STARS
# ==========================================
@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    payment_info = message.successful_payment
    user = message.from_user
    if payment_info.invoice_payload == "skin_generation_50":
        print(f"💰 Игрок {user.first_name} купил генерацию за {payment_info.total_amount} Stars!")
        await message.answer(f"✅ Оплата {payment_info.total_amount} ⭐️ успешно получена! Твоя генерация скина уже началась в игре.")

# ==========================================
# ЛОГИКА БОТА (КОМАНДЫ И СООБЩЕНИЯ)
# ==========================================
async def check_subscription(user_id, channel_username):
    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status in ["member", "creator", "administrator"]
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        return False

@dp.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

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

# ==========================================
# ЗАПУСК СЕРВЕРА И БОТА
# ==========================================
async def main():
    print("Бот запущен. Баннеры и кеш-бастер работают!")
    
    # 1. Настройка HTTP-сервера
    app = web.Application()
    import aiohttp_cors
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })
    
    # Добавляем маршруты для Mini App
    route_invoice = app.router.add_post('/api/create-invoice', create_invoice_api)
    route_sync = app.router.add_post('/api/sync', sync_api)
    
    cors.add(route_invoice)
    cors.add(route_sync)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 HTTP API Сервер запущен на порту {port}")
    
    # 2. Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())