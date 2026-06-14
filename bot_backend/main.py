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
# ⚠️ БЛОК ДЛЯ ТВОИХ ДАННЫХ
# ==========================================
YOUR_TELEGRAM_ID = None  # Твой ID (пока отключен)
CHANNEL_RU = "@robuxtap_ru"
CHANNEL_SNG = "@robuxtap_sng"
WEB_APP_URL = "https://grubot.vercel.app/"

BANNER_WELCOME = "https://images.unsplash.com/photo-1614680376573-df3480f0c6ff?q=80&w=1000&auto=format&fit=crop"
BANNER_GAME = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1000&auto=format&fit=crop"    

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==========================================
# БАЗА ДАННЫХ (РАСШИРЕННАЯ ПАМЯТЬ)
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
                    max_energy_level INTEGER DEFAULT 1,
                    studio_desk INTEGER DEFAULT 0,
                    studio_chair INTEGER DEFAULT 0,
                    studio_audio INTEGER DEFAULT 0,
                    studio_bed INTEGER DEFAULT 0,
                    studio_decor INTEGER DEFAULT 0,
                    owned_skins TEXT DEFAULT '["default"]',
                    current_skin TEXT DEFAULT 'default',
                    last_sync_time REAL DEFAULT 0
                )''')
conn.commit()

# ==========================================
# СИСТЕМА БЕЗОПАСНОСТИ (ТАМОЖНЯ)
# ==========================================
def validate_telegram_data(init_data: str, bot_token: str):
    try:
        parsed_data = dict(parse_qsl(init_data))
        received_hash = parsed_data.pop('hash', None)
        if not received_hash: return None

        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calculated_hash == received_hash:
            return json.loads(parsed_data.get('user', '{}'))
        return None
    except Exception as e:
        print(f"Ошибка валидации: {e}")
        return None

# ==========================================
# ЭКОНОМИКА: ФОРМУЛЫ И ЦЕНЫ
# ==========================================
def get_upgrade_cost(base_cost, current_level):
    """Формула цены для тех. бустов (Мультитап, Энергия, Бот)"""
    if base_cost == 5000 and current_level == 0:
        return 5000
    power = current_level - 1 if current_level > 0 else 0
    return base_cost * (2 ** power)

# Цены на скины (как в твоем JS)
SKIN_COSTS = {
    'coin': 50000,
    'diamond': 250000,
    'crown': 1000000
}

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
        studio_income_per_sec = data.get("studioIncome", 0) 
        
        user_data = validate_telegram_data(init_data, BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
            
        user_id = user_data.get("id")
        current_time = time.time()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_db = cursor.fetchone()
        
        if not user_db: return web.json_response({"error": "User not found in DB"}, status=404)
        
        # Индексы: 2=taps, 3=bonus, 4=multitap, 5=bot, 14=last_sync
        taps_balance = user_db[2]
        bonus_balance = user_db[3]
        multitap_level = user_db[4]
        bot_level = user_db[5]
        last_sync_time = user_db[14]
        
        # 1. Античит
        MAX_CLICKS_PER_SEC = 15
        elapsed_sec = elapsed_time_ms / 1000.0 if elapsed_time_ms > 0 else 3.0
        valid_clicks = min(clicks_claimed, int(MAX_CLICKS_PER_SEC * elapsed_sec))
        
        earned_from_taps = valid_clicks * multitap_level
        new_taps_balance = taps_balance + earned_from_taps
        
        # 2. Пассивный доход
        earned_passive = 0
        is_offline_reward = False
        
        if last_sync_time > 0:
            time_away_sec = current_time - last_sync_time
            if time_away_sec < 60:
                earned_passive = int(time_away_sec * studio_income_per_sec)
            else:
                if bot_level > 0:
                    active_offline_sec = min(time_away_sec, 10800) # Макс 3 часа
                    earned_passive = int(active_offline_sec * (studio_income_per_sec + bot_level))
                    is_offline_reward = True
        
        new_bonus_balance = bonus_balance + earned_passive
        
        # 3. Сохранение
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
        return web.json_response({"error": "Server error"}, status=500)


async def buy_api(request):
    """Единый маршрут для всех покупок (Бусты, Студия, Скины)"""
    try:
        data = await request.json()
        init_data = data.get("initData")
        buy_type = data.get("type") # 'tech' или 'skin'
        item_id = data.get("item_id") 
        
        user_data = validate_telegram_data(init_data, BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        user_id = user_data.get("id")
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_db = cursor.fetchone()
        if not user_db: return web.json_response({"error": "User not found"}, status=404)
        
        # Превращаем кортеж из БД в удобный словарь по названиям колонок
        cols = [desc[0] for desc in cursor.description]
        user_dict = dict(zip(cols, user_db))
        
        taps_bal = user_dict['taps_balance']
        bonus_bal = user_dict['bonus_balance']
        total_balance = taps_bal + bonus_bal
        
        cost = 0
        column_to_update = ""
        new_level = 0
        
        # ЛОГИКА ТЕХ. БУСТОВ
        if buy_type == "tech":
            if item_id == "multitap":
                cost = get_upgrade_cost(2000, user_dict['multitap_level'])
                column_to_update = "multitap_level"
                new_level = user_dict['multitap_level'] + 1
            elif item_id == "energy":
                cost = get_upgrade_cost(2000, user_dict['max_energy_level'])
                column_to_update = "max_energy_level"
                new_level = user_dict['max_energy_level'] + 1
            elif item_id == "bot":
                cost = get_upgrade_cost(5000, user_dict['bot_level'])
                column_to_update = "bot_level"
                new_level = user_dict['bot_level'] + 1
                
        # ЛОГИКА СКИНОВ
        elif buy_type == "skin":
            cost = SKIN_COSTS.get(item_id, 0)
            owned_skins = json.loads(user_dict['owned_skins'])
            if item_id in owned_skins:
                return web.json_response({"error": "Уже куплено"}, status=400)
            
            owned_skins.append(item_id)
            column_to_update = "owned_skins"
            new_level = json.dumps(owned_skins) # Сохраняем как строку JSON
            
        else:
            return web.json_response({"error": "Неизвестный тип покупки"}, status=400)

        # ПРОВЕРКА БАЛАНСА
        if cost == 0 or total_balance < cost:
            return web.json_response({"error": "Недостаточно средств или неверный предмет"}, status=400)
            
        # СПИСАНИЕ СРЕДСТВ (Сначала тратим бонусные $ROB, потом обычные)
        if bonus_bal >= cost:
            new_bonus_bal = bonus_bal - cost
            new_taps_bal = taps_bal
        else:
            remainder = cost - bonus_bal
            new_bonus_bal = 0
            new_taps_bal = taps_bal - remainder
            
        # ЗАПИСЬ В БАЗУ ДАННЫХ
        cursor.execute(f'''UPDATE users 
                          SET taps_balance = ?, bonus_balance = ?, {column_to_update} = ? 
                          WHERE user_id = ?''', 
                       (new_taps_bal, new_bonus_bal, new_level, user_id))
        conn.commit()
        
        print(f"🛍 Игрок {user_data.get('first_name')} купил {item_id} за {cost} $ROB")
        
        return web.json_response({
            "status": "success", 
            "new_taps_balance": new_taps_bal,
            "new_bonus_balance": new_bonus_bal
        })
        
    except Exception as e:
        print(f"Ошибка в /buy: {e}")
        return web.json_response({"error": "Server error"}, status=500)


async def create_invoice_api(request):
    try:
        prices = [LabeledPrice(label="Нейро-Скин", amount=50)]
        invoice_link = await bot.create_invoice_link(
            title="✨ Генерация ИИ-Скина",
            description="Оплата создания уникального скина в Нейро-кузнице",
            payload="skin_generation_50",
            provider_token="", 
            currency="XTR",
            prices=prices
        )
        return web.json_response({"invoice_url": invoice_link})
    except Exception as e:
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
        await message.answer(f"✅ Оплата {payment_info.total_amount} ⭐️ успешно получена!")

# ==========================================
# ЛОГИКА БОТА
# ==========================================
async def check_subscription(user_id, channel_username):
    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status in ["member", "creator", "administrator"]
    except Exception:
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
            try: await bot.send_message(ref_id, "🎉 <b>Новый друг по ссылке!</b>", parse_mode="HTML")
            except: pass

    is_sub_ru = await check_subscription(user_id, CHANNEL_RU)
    is_sub_sng = await check_subscription(user_id, CHANNEL_SNG)
    
    if is_sub_ru or is_sub_sng:
        cursor.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,))
        refs_count = cursor.fetchone()[0]
        current_time = int(time.time())
        custom_url = f"{WEB_APP_URL}?refs={refs_count}&v={current_time}"
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🎮 ИГРАТЬ (Tap to Earn)", web_app=WebAppInfo(url=custom_url)))
        
        text = f"🚀 <b>С возвращением, {first_name}!</b>\n\n👇 <b>Жми на кнопку ниже:</b>"
        await message.answer_photo(photo=BANNER_GAME, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🇷🇺 Канал (РФ)", url=f"https://t.me/{CHANNEL_RU[1:]}"))
        builder.row(types.InlineKeyboardButton(text="🌍 Канал (СНГ/Другие)", url=f"https://t.me/{CHANNEL_SNG[1:]}"))
        builder.row(types.InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub"))
        
        text = f"👋 <b>Привет, {first_name}!</b>\n\n🔒 Подпишись для доступа:"
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
        
        await callback.message.delete()
        await bot.send_photo(chat_id=callback.message.chat.id, photo=BANNER_GAME, caption=f"✅ <b>Отлично, {first_name}!</b>", reply_markup=game_builder.as_markup(), parse_mode="HTML")
    else:
        await callback.answer("❌ Ты еще не подписался!", show_alert=True)

# ==========================================
# ЗАПУСК СЕРВЕРА И БОТА
# ==========================================
async def main():
    print("Бот запущен!")
    
    app = web.Application()
    import aiohttp_cors
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*")
    })
    
    # Регистрация маршрутов
    route_sync = app.router.add_post('/api/sync', sync_api)
    route_buy = app.router.add_post('/api/buy', buy_api)
    route_invoice = app.router.add_post('/api/create-invoice', create_invoice_api)
    
    cors.add(route_sync)
    cors.add(route_buy)
    cors.add(route_invoice)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 HTTP API Сервер запущен на порту {port}")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())