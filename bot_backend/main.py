import asyncio
import os
import time
import json
import hashlib
import hmac
from urllib.parse import parse_qsl
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import CommandStart, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo, LabeledPrice, PreCheckoutQuery
import aiosqlite  # Асинхронная работа с БД
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ==========================================
# ⚠️ НАСТРОЙКИ
# ==========================================
YOUR_TELEGRAM_ID = None  
CHANNEL_RU = "@robuxtap_ru"
CHANNEL_SNG = "@robuxtap_sng"
WEB_APP_URL = "https://grubot.vercel.app/"

BANNER_WELCOME = "https://images.unsplash.com/photo-1614680376573-df3480f0c6ff?q=80&w=1000&auto=format&fit=crop"
BANNER_GAME = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1000&auto=format&fit=crop"    

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
DB_NAME = 'database.db'

# ==========================================
# ЭКОНОМИКА: ФОРМУЛЫ И ЦЕНЫ
# ==========================================
def get_upgrade_cost(base_cost, current_level):
    if base_cost == 5000 and current_level == 0: return 5000
    power = current_level - 1 if current_level > 0 else 0
    return base_cost * (2 ** power)

SKIN_COSTS = {'coin': 50000, 'diamond': 250000, 'crown': 1000000}

# Синхронизировано с фронтендом!
ROOM_LEVELS = {
    1: {'cost': 15000, 'income': 3},
    2: {'cost': 500000, 'income': 6},
    3: {'cost': 1500000, 'income': 12}
}

# ==========================================
# ИНИЦИАЛИЗАЦИЯ БД (Асинхронная)
# ==========================================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Включаем WAL-режим (Write-Ahead Logging) для ускорения записи в 3-5 раз
        await db.execute('PRAGMA journal_mode=WAL;')
        
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referrer_id INTEGER,
            first_name TEXT DEFAULT 'Игрок',
            username TEXT DEFAULT '',
            squad_id TEXT DEFAULT '',
            taps_balance INTEGER DEFAULT 0,
            bonus_balance INTEGER DEFAULT 0,
            multitap_level INTEGER DEFAULT 1,
            bot_level INTEGER DEFAULT 0,
            max_energy_level INTEGER DEFAULT 1,
            current_room_level INTEGER DEFAULT 0,
            owned_skins TEXT DEFAULT '["default"]',
            current_skin TEXT DEFAULT 'default',
            last_sync_time REAL DEFAULT 0,
            last_squad_join_time REAL DEFAULT 0
        )''')
        await db.commit()

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
# HTTP API ДЛЯ МИНИ-АППА
# ==========================================
async def sync_api(request):
    try:
        data = await request.json()
        init_data = data.get("initData")
        clicks_claimed = data.get("clicks", 0)
        
        user_data = validate_telegram_data(init_data, BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
            
        user_id = user_data.get("id")
        first_name = user_data.get("first_name", "Игрок")
        username = user_data.get("username", "")
        current_time = time.time()
        
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT taps_balance, bonus_balance, multitap_level, bot_level, current_room_level, last_sync_time, squad_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
                user_db = await cursor.fetchone()
                
            if not user_db: return web.json_response({"error": "User not found"}, status=404)
            
            taps_bal, bonus_bal, multi_lvl, bot_lvl, room_lvl, last_sync, squad_id = user_db
            
            # 1. ЗАЩИТА АВТОКЛИКЕРА: Считаем реальное время на сервере
            elapsed_sec = current_time - last_sync if last_sync > 0 else 0
            MAX_CLICKS_PER_SEC = 15
            
            # Даем небольшой буфер (например, 3 секунды), если игрок только зашел
            safe_time = max(elapsed_sec, 3.0) 
            max_possible_clicks = int(MAX_CLICKS_PER_SEC * safe_time)
            
            # Берем минимальное значение: либо сколько он реально накликал, либо лимит
            valid_clicks = min(clicks_claimed, max_possible_clicks)
            earned_from_taps = valid_clicks * multi_lvl
            
            # 2. ЗАЩИТА ПАССИВНОГО ДОХОДА: Сервер сам знает, сколько приносит комната
            earned_passive = 0
            is_offline_reward = False
            studio_income_per_sec = ROOM_LEVELS.get(room_lvl, {}).get('income', 0)
            
            if last_sync > 0 and elapsed_sec > 0:
                if elapsed_sec < 60:
                    # Игрок онлайн, начисляем пассивный доход за эти секунды
                    earned_passive = int(elapsed_sec * studio_income_per_sec)
                else:
                    # Офлайн логика (работает только если куплен Авто-Бот)
                    if bot_lvl > 0:
                        active_offline_sec = min(elapsed_sec, 10800) # Максимум 3 часа
                        earned_passive = int(active_offline_sec * (studio_income_per_sec + bot_lvl))
                        is_offline_reward = True
            
            new_taps_bal = taps_bal + earned_from_taps
            new_bonus_bal = bonus_bal + earned_passive
            
            await db.execute('''UPDATE users 
                              SET taps_balance = ?, bonus_balance = ?, last_sync_time = ?, first_name = ?, username = ?
                              WHERE user_id = ?''', 
                           (new_taps_bal, new_bonus_bal, current_time, first_name, username, user_id))
            await db.commit()
            
        return web.json_response({
            "status": "success", "new_taps_balance": new_taps_bal, "new_bonus_balance": new_bonus_bal,
            "earned_offline": earned_passive if is_offline_reward else 0, "current_squad": squad_id
        })
    except Exception as e:
        print(f"Sync error: {e}")
        return web.json_response({"error": "Server error"}, status=500)


async def buy_api(request):
    try:
        data = await request.json()
        init_data = data.get("initData")
        buy_type = data.get("type") 
        
        user_data = validate_telegram_data(init_data, BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        user_id = user_data.get("id")
        
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                user_db = await cursor.fetchone()
                
            if not user_db: return web.json_response({"error": "User not found"}, status=404)
            
            taps_bal = user_db['taps_balance']
            bonus_bal = user_db['bonus_balance']
            total_balance = taps_bal + bonus_bal
            
            cost = 0; column_to_update = ""; new_value = 0
            
            if buy_type == "tech":
                item_id = data.get("item_id")
                if item_id == "multitap": 
                    cost = get_upgrade_cost(2000, user_db['multitap_level'])
                    column_to_update = "multitap_level"; new_value = user_db['multitap_level'] + 1
                elif item_id == "energy": 
                    cost = get_upgrade_cost(2000, user_db['max_energy_level'])
                    column_to_update = "max_energy_level"; new_value = user_db['max_energy_level'] + 1
                elif item_id == "bot": 
                    cost = get_upgrade_cost(5000, user_db['bot_level'])
                    column_to_update = "bot_level"; new_value = user_db['bot_level'] + 1
            
            elif buy_type == "skin":
                item_id = data.get("item_id")
                cost = SKIN_COSTS.get(item_id, 0)
                owned_skins = json.loads(user_db['owned_skins'])
                if item_id in owned_skins: return web.json_response({"error": "Уже куплено"}, status=400)
                owned_skins.append(item_id)
                column_to_update = "owned_skins"; new_value = json.dumps(owned_skins)
            
            elif buy_type == "room_upgrade":
                level_id = data.get("level")
                if level_id not in ROOM_LEVELS: return web.json_response({"error": "Неверный уровень комнаты"}, status=400)
                if user_db['current_room_level'] >= level_id: return web.json_response({"error": "Этот уровень уже установлен"}, status=400)
                if level_id > user_db['current_room_level'] + 1: return web.json_response({"error": "Нельзя перепрыгивать уровни"}, status=400)
                
                cost = ROOM_LEVELS[level_id]['cost']
                column_to_update = "current_room_level"
                new_value = level_id
                
            else: return web.json_response({"error": "Неизвестный тип"}, status=400)

            if cost > 0 and total_balance < cost: return web.json_response({"error": "Недостаточно средств"}, status=400)
                
            # Расчет списания
            if bonus_bal >= cost: 
                new_bonus_bal = bonus_bal - cost; new_taps_bal = taps_bal
            else: 
                remainder = cost - bonus_bal; new_bonus_bal = 0; new_taps_bal = taps_bal - remainder
                
            # АТОМАРНОЕ ОБНОВЛЕНИЕ (защита от багов и хаков)
            await db.execute(f'''UPDATE users 
                                 SET taps_balance = ?, bonus_balance = ?, {column_to_update} = ? 
                                 WHERE user_id = ? AND (taps_balance + bonus_balance) >= ?''', 
                             (new_taps_bal, new_bonus_bal, new_value, user_id, cost))
            await db.commit()
            
            return web.json_response({"status": "success", "new_taps_balance": new_taps_bal, "new_bonus_balance": new_bonus_bal})
    except Exception as e:
        print(f"Buy error: {e}")
        return web.json_response({"error": "Server error"}, status=500)


# --- СКВАДЫ И ЛИДЕРБОРД ---
async def create_squad_api(request):
    try:
        data = await request.json()
        init_data = data.get("initData")
        channel_username = data.get("channel", "").strip()
        
        user_data = validate_telegram_data(init_data, BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        
        user_id = user_data.get("id")
        if not channel_username.startswith("@"):
            channel_username = "@" + channel_username

        try:
            member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
            if member.status not in ["administrator", "creator"]:
                return web.json_response({"error": "Вы не являетесь администратором этого канала!"}, status=400)
        except Exception:
            return web.json_response({"error": "Добавьте бота в администраторы канала (без прав)!"}, status=400)

        link = f"https://t.me/grutap_robot?start=squad_{channel_username[1:]}"
        return web.json_response({"status": "success", "link": link})
    except Exception:
        return web.json_response({"error": "Ошибка на сервере"}, status=500)

async def leaderboard_api(request):
    try:
        data = await request.json()
        init_data = data.get("initData")
        tab = data.get("tab", "players")
        
        user_data = validate_telegram_data(init_data, BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        req_user_id = user_data.get("id")
        
        async with aiosqlite.connect(DB_NAME) as db:
            if tab == "players":
                async with db.execute('''SELECT user_id, first_name, username, (taps_balance + bonus_balance) as score
                                         FROM users ORDER BY score DESC LIMIT 50''') as cursor:
                    rows = await cursor.fetchall()
                players = [{"id": r[0], "name": r[1] or "Аноним", "username": r[2], "score": r[3], "isMe": r[0] == req_user_id} for r in rows]
                return web.json_response({"status": "success", "list": players, "tab": "players"})
            
            elif tab == "squads":
                async with db.execute('''SELECT squad_id, COUNT(user_id) as members, SUM(taps_balance + bonus_balance) as total_score
                                         FROM users WHERE squad_id != '' GROUP BY squad_id ORDER BY total_score DESC LIMIT 50''') as cursor:
                    rows = await cursor.fetchall()
                
                async with db.execute("SELECT squad_id FROM users WHERE user_id = ?", (req_user_id,)) as cursor:
                    user_squad_row = await cursor.fetchone()
                    user_squad = user_squad_row[0] if user_squad_row else ""
                
                squads = [{"id": r[0], "members": r[1], "score": r[2], "isMySquad": r[0] == user_squad} for r in rows]
                return web.json_response({"status": "success", "list": squads, "tab": "squads"})
                
    except Exception as e:
        print(f"Leaderboard error: {e}")
        return web.json_response({"error": "Server error"}, status=500)


async def create_invoice_api(request):
    try:
        prices = [LabeledPrice(label="Нейро-Скин", amount=50)]
        invoice_link = await bot.create_invoice_link(title="✨ Генерация ИИ-Скина", description="Оплата создания уникального скина", payload="skin_generation_50", provider_token="", currency="XTR", prices=prices)
        return web.json_response({"invoice_url": invoice_link})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

# ==========================================
# ОБРАБОТЧИКИ БОТА
# ==========================================
@dp.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    if message.successful_payment.invoice_payload == "skin_generation_50":
        await message.answer(f"✅ Оплата {message.successful_payment.total_amount} ⭐️ успешно получена!")

async def check_subscription(user_id, channel_username):
    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status in ["member", "creator", "administrator"]
    except: return False

@dp.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    current_time = time.time()

    ref_id = None
    squad_id = ""
    
    if command.args:
        if command.args.startswith("ref_"):
            ref_id_str = command.args.split("_")[1]
            if ref_id_str.isdigit() and int(ref_id_str) != user_id: ref_id = int(ref_id_str)
        elif command.args.startswith("squad_"):
            squad_id = "@" + command.args.split("_")[1]

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user_data = await cursor.fetchone()
        
        if not user_data:
            join_time = current_time if squad_id else 0
            await db.execute("INSERT INTO users (user_id, referrer_id, first_name, squad_id, last_squad_join_time) VALUES (?, ?, ?, ?, ?)", 
                             (user_id, ref_id, first_name, squad_id, join_time))
            await db.commit()
            if ref_id:
                try: await bot.send_message(ref_id, "🎉 <b>Новый друг по ссылке!</b>", parse_mode="HTML")
                except: pass
            if squad_id:
                await message.answer(f"🎉 Вы успешно вступили в сквад <b>{squad_id}</b>!", parse_mode="HTML")
        else:
            if squad_id and user_data[4] != squad_id:
                last_join = user_data[14] # Индекс last_squad_join_time
                if current_time - last_join >= 604800 or last_join == 0:
                    await db.execute("UPDATE users SET squad_id = ?, last_squad_join_time = ? WHERE user_id = ?", (squad_id, current_time, user_id))
                    await db.commit()
                    await message.answer(f"🎉 Вы успешно перешли в сквад <b>{squad_id}</b>!", parse_mode="HTML")
                else:
                    days_left = int((604800 - (current_time - last_join)) / 86400) + 1
                    await message.answer(f"⏳ Слишком частая смена сквада!\nСледующий переход будет доступен через <b>{days_left} дн.</b>", parse_mode="HTML")

        async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,)) as cursor:
            refs_count_row = await cursor.fetchone()
            refs_count = refs_count_row[0] if refs_count_row else 0

    is_sub_ru = await check_subscription(user_id, CHANNEL_RU)
    is_sub_sng = await check_subscription(user_id, CHANNEL_SNG)
    
    if is_sub_ru or is_sub_sng:
        custom_url = f"{WEB_APP_URL}?refs={refs_count}&v={int(current_time)}"
        
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🎮 ИГРАТЬ (Tap to Earn)", web_app=WebAppInfo(url=custom_url)))
        await message.answer_photo(photo=BANNER_GAME, caption=f"🚀 <b>С возвращением, {first_name}!</b>\n\n👇 <b>Жми на кнопку ниже:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🇷🇺 Канал (РФ)", url=f"https://t.me/{CHANNEL_RU[1:]}"))
        builder.row(types.InlineKeyboardButton(text="🌍 Канал (СНГ/Другие)", url=f"https://t.me/{CHANNEL_SNG[1:]}"))
        builder.row(types.InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub"))
        await message.answer_photo(photo=BANNER_WELCOME, caption=f"👋 <b>Привет, {first_name}!</b>\n\n🔒 Подпишись для доступа:", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "check_sub")
async def process_check(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if await check_subscription(user_id, CHANNEL_RU) or await check_subscription(user_id, CHANNEL_SNG):
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,)) as cursor:
                refs_count = (await cursor.fetchone())[0]
                
        custom_url = f"{WEB_APP_URL}?refs={refs_count}&v={int(time.time())}"
        game_builder = InlineKeyboardBuilder()
        game_builder.row(types.InlineKeyboardButton(text="🎮 ИГРАТЬ (Tap to Earn)", web_app=WebAppInfo(url=custom_url)))
        await callback.message.delete()
        await bot.send_photo(chat_id=callback.message.chat.id, photo=BANNER_GAME, caption=f"✅ <b>Отлично, {callback.from_user.first_name}!</b>", reply_markup=game_builder.as_markup(), parse_mode="HTML")
    else:
        await callback.answer("❌ Ты еще не подписался!", show_alert=True)

# ==========================================
# ЗАПУСК
# ==========================================
async def main():
    print("Инициализация базы данных...")
    await init_db()
    
    print("Бот запущен!")
    app = web.Application()
    import aiohttp_cors
    cors = aiohttp_cors.setup(app, defaults={"*": aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*")})
    
    cors.add(app.router.add_post('/api/sync', sync_api))
    cors.add(app.router.add_post('/api/buy', buy_api))
    cors.add(app.router.add_post('/api/create-squad', create_squad_api))
    cors.add(app.router.add_post('/api/leaderboard', leaderboard_api))
    cors.add(app.router.add_post('/api/create-invoice', create_invoice_api))
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    await web.TCPSite(runner, '0.0.0.0', port).start()
    print(f"🌐 HTTP API Сервер запущен на порту {port}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())