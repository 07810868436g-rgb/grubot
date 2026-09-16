import asyncio
import os
import time
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from urllib.parse import parse_qsl
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import CommandStart, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo
import asyncpg
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# --- НАСТРОЙКИ КАНАЛОВ ---
PAYOUT_CHANNEL_ID = "-1000000000000" # ВСТАВЬ СЮДА ID ЗАКРЫТОГО КАНАЛА ДЛЯ ВЫВОДОВ
CHANNEL_RU = "@robuxtap_ru"
CHANNEL_SNG = "@robuxtap_sng"
WEB_APP_URL = "https://grubot.vercel.app/"

SPONSOR_CHANNELS = {
    1: "@grusponsors",
    2: "@grulvl",
    3: "@grufans"
    # 4-й канал удален под публичный канал выплат
}

BANNER_GAME = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1000&auto=format&fit=crop"    

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db_pool = None 

# Очередь для честного PvP (ставка: (user_id, score, timestamp))
pvp_queue = {}

async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, statement_cache_size=0)
    
    async with db_pool.acquire() as conn:
        await conn.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            game_id SERIAL UNIQUE,
            referrer_id BIGINT,
            first_name TEXT DEFAULT 'Игрок',
            username TEXT DEFAULT '',
            taps_balance BIGINT DEFAULT 0,
            bonus_balance BIGINT DEFAULT 0,
            multitap_level INTEGER DEFAULT 1,
            bot_level INTEGER DEFAULT 0,
            max_energy_level INTEGER DEFAULT 1,
            last_sync_time DOUBLE PRECISION DEFAULT 0,
            total_play_time DOUBLE PRECISION DEFAULT 0,
            withdraw_count INTEGER DEFAULT 0,
            roblox_nick TEXT DEFAULT '',
            last_play_date TEXT DEFAULT '',
            daily_streak INTEGER DEFAULT 0,
            last_claim_date TEXT DEFAULT '',
            claimed_sponsors TEXT DEFAULT '[]',
            daily_taps BIGINT DEFAULT 0,
            daily_quest_claimed INTEGER DEFAULT 0,
            turbine_charges INTEGER DEFAULT 1,
            last_turbine_date TEXT DEFAULT '',
            language TEXT DEFAULT 'ru'
        )''')
        
        # Добавляем колонки, если таблица старая
        cols = ["game_id SERIAL UNIQUE", "total_play_time DOUBLE PRECISION DEFAULT 0", "withdraw_count INTEGER DEFAULT 0", "roblox_nick TEXT DEFAULT ''"]
        for col in cols:
            try: await conn.execute(f"ALTER TABLE users ADD COLUMN {col}")
            except Exception: pass

def validate_telegram_data(init_data: str, bot_token: str):
    try:
        parsed_data = dict(parse_qsl(init_data))
        received_hash = parsed_data.pop('hash', None)
        auth_date = int(parsed_data.get('auth_date', 0))
        
        # АНТИЧИТ: Запрет старых сессий (защита от кражи ссылки, макс 24 часа)
        if time.time() - auth_date > 86400: return None
        if not received_hash: return None
        
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calculated_hash == received_hash:
            return json.loads(parsed_data.get('user', '{}'))
        return None
    except Exception: return None

async def check_subscription(user_id, channel_username):
    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status in ["member", "creator", "administrator"]
    except Exception: return False

def get_upgrade_cost(base_cost, current_level):
    if base_cost == 5000 and current_level == 0: return 5000
    power = current_level - 1 if current_level > 0 else 0
    return base_cost * (2 ** power)

# ==========================================
# ФУНКЦИИ API 
# ==========================================

async def sync_api(request):
    try:
        data = await request.json()
        user_data = validate_telegram_data(data.get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Сессия устарела. Перезапустите бота!"}, status=401)
            
        user_id = user_data.get("id")
        is_premium = user_data.get("is_premium", False)
        max_turbine_charges = 2 if is_premium else 1
        standard_clicks = data.get("standard_clicks", 0)
        current_time = time.time()
        current_date = time.strftime('%Y-%m-%d')
        
        async with db_pool.acquire() as conn:
            user_db = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
            if not user_db: return web.json_response({"error": "User not found"}, status=404)
            
            last_play_date = user_db['last_play_date']
            daily_taps = user_db['daily_taps']
            daily_quest_claimed = user_db['daily_quest_claimed']
            turbine_charges = user_db['turbine_charges']
            last_turbine_date = user_db['last_turbine_date']
            
            # Обновление дней
            if last_play_date != current_date:
                last_play_date = current_date; daily_taps = 0; daily_quest_claimed = 0
            if last_turbine_date != current_date:
                turbine_charges = max_turbine_charges; last_turbine_date = current_date

            # Подсчет времени в игре (Античит: не больше 10 сек за один синк)
            elapsed_sec = current_time - user_db['last_sync_time'] if user_db['last_sync_time'] > 0 else 0
            play_time_add = min(elapsed_sec, 10.0) if user_db['last_sync_time'] > 0 else 0
            new_total_time = user_db['total_play_time'] + play_time_add

            # Античит кликов
            MAX_CLICKS_PER_SEC = 20
            safe_time = max(elapsed_sec, 2.0)
            valid_clicks = min(standard_clicks, int(MAX_CLICKS_PER_SEC * safe_time))
            earned_from_taps = valid_clicks * user_db['multitap_level']
            daily_taps += earned_from_taps
            
            # Пассивный доход
            earned_passive = 0; is_offline_reward = False
            if user_db['last_sync_time'] > 0 and elapsed_sec > 60 and user_db['bot_level'] > 0:
                active_offline_sec = min(elapsed_sec, 10800) # Макс 3 часа
                earned_passive = int(active_offline_sec * user_db['bot_level'])
                is_offline_reward = True
            
            new_taps_bal = user_db['taps_balance'] + earned_from_taps
            new_bonus_bal = user_db['bonus_balance'] + earned_passive
            
            await conn.execute('''UPDATE users 
                              SET taps_balance = $1, bonus_balance = $2, last_sync_time = $3, total_play_time = $4,
                                  last_play_date = $5, daily_taps = $6, daily_quest_claimed = $7,
                                  turbine_charges = $8, last_turbine_date = $9
                              WHERE user_id = $10''', 
                           new_taps_bal, new_bonus_bal, current_time, new_total_time, last_play_date, 
                           daily_taps, daily_quest_claimed, turbine_charges, last_turbine_date, user_id)
            
            # Считаем рефов
            r = await conn.fetchrow("SELECT COUNT(*) as count FROM users WHERE referrer_id = $1", user_id)
            refs_count = r['count'] if r else 0

        return web.json_response({
            "status": "success", "new_taps_balance": new_taps_bal, "new_bonus_balance": new_bonus_bal,
            "earned_offline": earned_passive if is_offline_reward else 0,
            "daily_streak": user_db['daily_streak'], "last_claim_date": user_db['last_claim_date'],
            "claimed_sponsors": user_db['claimed_sponsors'], "daily_taps": daily_taps, "daily_quest_claimed": daily_quest_claimed,
            "turbine_charges": turbine_charges, "max_charges": max_turbine_charges,
            "game_id": f"G{str(user_db['game_id']).zfill(5)}", "total_play_time": new_total_time, "refs_count": refs_count
        })
    except Exception as e: return web.json_response({"error": "Server error"}, status=500)

async def turbine_claim_api(request):
    try:
        data = await request.json()
        user_data = validate_telegram_data(data.get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        
        user_id = user_data.get("id")
        earned = int(data.get("amount", 0))
        
        # АНТИЧИТ ТУРБИНЫ: Физически невозможно выдуть больше 2000 очков за 15 сек (эквивалент 0.2 $ROB)
        if earned < 0 or earned > 2000: return web.json_response({"error": "Превышен лимит децибелов (Античит)!"}, status=400)

        async with db_pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow("SELECT turbine_charges, bonus_balance FROM users WHERE user_id = $1 FOR UPDATE", user_id)
                if not row or row['turbine_charges'] <= 0: return web.json_response({"error": "Заряды турбины исчерпаны!"}, status=400)
                
                new_charges = row['turbine_charges'] - 1
                new_bonus = row['bonus_balance'] + earned
                await conn.execute("UPDATE users SET turbine_charges = $1, bonus_balance = $2 WHERE user_id = $3", new_charges, new_bonus, user_id)
                
            return web.json_response({"status": "success", "new_bonus_balance": new_bonus, "turbine_charges": new_charges})
    except Exception as e: return web.json_response({"error": str(e)}, status=500)

async def pvp_result_api(request):
    try:
        data = await request.json()
        user_data = validate_telegram_data(data.get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        
        user_id = user_data.get("id")
        bet = int(data.get("bet", 0))
        score = int(data.get("score", 0))
        
        if bet < 10000: return web.json_response({"error": "Минимальная ставка 1.0000 $ROB (10000)!"}, status=400)

        async with db_pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow("SELECT taps_balance, bonus_balance FROM users WHERE user_id = $1 FOR UPDATE", user_id)
                total_bal = row['taps_balance'] + row['bonus_balance']
                if total_bal < bet: return web.json_response({"error": "Недостаточно средств!"}, status=400)
                
                # Реальный подбор игроков (Серверная очередь)
                global pvp_queue
                opponent = pvp_queue.get(bet)
                
                if opponent and opponent['user_id'] != user_id:
                    # Оппонент найден, решаем бой
                    del pvp_queue[bet]
                    is_win = score >= opponent['score']
                    
                    if is_win:
                        profit = int(bet * 0.95) # 5% комиссия
                        await conn.execute("UPDATE users SET bonus_balance = bonus_balance + $1 WHERE user_id = $2", profit, user_id)
                    else:
                        loss = bet
                        if row['bonus_balance'] >= loss: await conn.execute("UPDATE users SET bonus_balance = bonus_balance - $1 WHERE user_id = $2", loss, user_id)
                        else: await conn.execute("UPDATE users SET taps_balance = taps_balance - $1, bonus_balance = 0 WHERE user_id = $2", loss - row['bonus_balance'], user_id)
                    
                    return web.json_response({"status": "success", "is_win": is_win})
                else:
                    # Ставим в очередь
                    pvp_queue[bet] = {'user_id': user_id, 'score': score, 'time': time.time()}
                    
                    # Ожидание результатов от другого игрока (упрощенный Long Polling)
                    await asyncio.sleep(3)
                    
                    if bet not in pvp_queue or pvp_queue[bet]['user_id'] != user_id:
                        # Нас кто-то забрал из очереди (бой прошел, значит мы проиграли, т.к. победитель получает ответ сразу)
                        loss = bet
                        if row['bonus_balance'] >= loss: await conn.execute("UPDATE users SET bonus_balance = bonus_balance - $1 WHERE user_id = $2", loss, user_id)
                        else: await conn.execute("UPDATE users SET taps_balance = taps_balance - $1, bonus_balance = 0 WHERE user_id = $2", loss - row['bonus_balance'], user_id)
                        return web.json_response({"status": "success", "is_win": False})
                    else:
                        # Никто не пришел, возвращаем ставку и убираем из очереди
                        del pvp_queue[bet]
                        return web.json_response({"error": "Противник не найден. Ставка возвращена.", "refund": True}, status=400)

    except Exception as e: return web.json_response({"error": str(e)}, status=500)

async def buy_api(request):
    try:
        data = await request.json()
        user_data = validate_telegram_data(data.get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        user_id = user_data.get("id"); buy_type = data.get("type") 
        
        async with db_pool.acquire() as conn:
            async with conn.transaction(): # Транзакция для защиты от автокликера (Double Spend)
                user_db = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1 FOR UPDATE", user_id)
                taps_bal = int(user_db['taps_balance']); bonus_bal = int(user_db['bonus_balance'])
                total_balance = taps_bal + bonus_bal; cost = 0; column_to_update = ""; new_value = 0
                
                if buy_type == "tech":
                    item_id = data.get("item_id")
                    if item_id == "multitap": cost = get_upgrade_cost(20000, int(user_db['multitap_level'])); column_to_update = "multitap_level"; new_value = int(user_db['multitap_level']) + 1
                    elif item_id == "energy": cost = get_upgrade_cost(20000, int(user_db['max_energy_level'])); column_to_update = "max_energy_level"; new_value = int(user_db['max_energy_level']) + 1
                    elif item_id == "bot": cost = get_upgrade_cost(50000, int(user_db['bot_level'])); column_to_update = "bot_level"; new_value = int(user_db['bot_level']) + 1
                
                if cost > 0 and total_balance < cost: return web.json_response({"error": "Недостаточно средств"}, status=400)
                if bonus_bal >= cost: new_bonus_bal = bonus_bal - cost; new_taps_bal = taps_bal
                else: remainder = cost - bonus_bal; new_bonus_bal = 0; new_taps_bal = taps_bal - remainder
                
                if column_to_update: await conn.execute(f'UPDATE users SET taps_balance = $1, bonus_balance = $2, {column_to_update} = $3 WHERE user_id = $4', new_taps_bal, new_bonus_bal, new_value, user_id)
                return web.json_response({"status": "success", "new_taps_balance": new_taps_bal, "new_bonus_balance": new_bonus_bal})
    except Exception as e: return web.json_response({"error": str(e)}, status=500)

async def withdraw_api(request):
    try:
        data = await request.json()
        user_data = validate_telegram_data(data.get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        user_id = user_data.get("id")
        roblox_nick = data.get("roblox_nick", "").strip()
        username = user_data.get("username", "NoName")
        
        if not roblox_nick: return web.json_response({"error": "Введите Roblox Ник!"}, status=400)

        async with db_pool.acquire() as conn:
            async with conn.transaction():
                user_db = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1 FOR UPDATE", user_id)
                t_bal = user_db['taps_balance']; b_bal = user_db['bonus_balance']
                total_bal = t_bal + b_bal
                
                # УСЛОВИЯ ВЫВОДА
                r = await conn.fetchrow("SELECT COUNT(*) as count FROM users WHERE referrer_id = $1", user_id)
                refs_count = r['count'] if r else 0
                
                if total_bal < 500000: return web.json_response({"error": "Минимум 50.0000 $ROB!"}, status=400)
                if refs_count < 10: return web.json_response({"error": "Нужно 10 друзей!"}, status=400)
                if user_db['total_play_time'] < 7200: return web.json_response({"error": "Отыграйте 2 часа!"}, status=400)
                
                # Списание и обновление ника
                await conn.execute("UPDATE users SET taps_balance = 0, bonus_balance = 0, roblox_nick = $1, withdraw_count = withdraw_count + 1 WHERE user_id = $2", roblox_nick, user_id)
                
                # Отправка заявки в закрытый канал
                game_id = f"G{str(user_db['game_id']).zfill(5)}"
                play_hours = round(user_db['total_play_time'] / 3600, 1)
                amount_formatted = f"{(total_bal / 10000):.4f}"
                
                msg = f"🚨 **ЗАЯВКА НА ВЫВОД**\n🆔 **Аккаунт:** `{game_id}`\n👤 **TG:** @{username} ({user_id})\n🎮 **Roblox Ник:** `{roblox_nick}`\n💰 **Сумма:** {amount_formatted} $ROB\n⏱ **Время в игре:** {play_hours} ч.\n👥 **Друзей:** {refs_count}"
                
                builder = InlineKeyboardBuilder()
                builder.row(types.InlineKeyboardButton(text="✅ Выплачено", callback_data=f"pay_{user_id}"))
                builder.row(types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user_id}_{total_bal}"))
                
                try: await bot.send_message(chat_id=PAYOUT_CHANNEL_ID, text=msg, reply_markup=builder.as_markup(), parse_mode="Markdown")
                except Exception as e: print("Ошибка отправки заявки:", e)
                
                return web.json_response({"status": "success"})
    except Exception as e: return web.json_response({"error": str(e)}, status=500)

async def claim_daily_quest_api(request):
    try:
        user_data = validate_telegram_data((await request.json()).get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        user_id = user_data.get("id")
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT daily_taps, daily_quest_claimed, bonus_balance FROM users WHERE user_id = $1", user_id)
            if row['daily_taps'] < 5000: return web.json_response({"error": "Цель еще не выполнена!"}, status=400)
            if row['daily_quest_claimed'] == 1: return web.json_response({"error": "Награда уже получена!"}, status=400)
            new_bonus = row['bonus_balance'] + 10000 # 1.0000 $ROB
            await conn.execute("UPDATE users SET daily_quest_claimed = 1, bonus_balance = $1 WHERE user_id = $2", new_bonus, user_id)
            return web.json_response({"status": "success", "new_bonus_balance": new_bonus})
    except Exception: return web.json_response({"error": "Error"}, status=500)

async def daily_claim_api(request):
    try:
        user_data = validate_telegram_data((await request.json()).get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        user_id = user_data.get("id"); today_str = datetime.now().strftime('%Y-%m-%d')
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT daily_streak, last_claim_date, bonus_balance FROM users WHERE user_id = $1", user_id)
            streak = int(row['daily_streak'] or 0); last_claim = row['last_claim_date']
            if last_claim == today_str: return web.json_response({"error": "Сегодня вы уже забрали награду!"}, status=400)
            if last_claim == yesterday_str: streak = (streak % 7) + 1
            else: streak = 1  
            reward = streak * 10000 # 1 $ROB за день * стрик
            new_bonus = int(row['bonus_balance'] or 0) + reward
            await conn.execute("UPDATE users SET daily_streak = $1, last_claim_date = $2, bonus_balance = $3 WHERE user_id = $4", streak, today_str, new_bonus, user_id)
            return web.json_response({"status": "success", "daily_streak": streak, "last_claim_date": today_str, "new_bonus_balance": new_bonus, "reward_received": reward})
    except Exception: return web.json_response({"error": "Error"}, status=500)

async def claim_sponsor_api(request):
    try:
        data = await request.json()
        user_data = validate_telegram_data(data.get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        user_id = user_data.get("id"); sponsor_id = int(data.get("sponsor_id", 0))
        channel = SPONSOR_CHANNELS.get(sponsor_id)
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT claimed_sponsors, bonus_balance FROM users WHERE user_id = $1", user_id)
            claimed = json.loads(row['claimed_sponsors'] or '[]'); new_bonus = int(row['bonus_balance'] or 0) + 5000 # 0.5000 $ROB
            if sponsor_id in claimed: return web.json_response({"error": "Награда уже получена!"}, status=400)
            if not await check_subscription(user_id, channel): return web.json_response({"error": f"Вы не подписаны!"}, status=400)
            claimed.append(sponsor_id)
            await conn.execute("UPDATE users SET claimed_sponsors = $1, bonus_balance = $2 WHERE user_id = $3", json.dumps(claimed), new_bonus, user_id)
            return web.json_response({"status": "success", "claimed_sponsors": json.dumps(claimed), "new_bonus_balance": new_bonus})
    except Exception: return web.json_response({"error": "Error"}, status=500)

async def leaderboard_api(request):
    try:
        data = await request.json()
        user_data = validate_telegram_data(data.get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        req_user_id = user_data.get("id")
        async with db_pool.acquire() as conn:
            rows = await conn.fetch('SELECT user_id, first_name, username, (taps_balance + bonus_balance) as score FROM users ORDER BY score DESC LIMIT 50')
            players = [{"id": r['user_id'], "name": r['first_name'] or "Аноним", "username": r['username'], "score": r['score'], "isMe": r['user_id'] == req_user_id} for r in rows]
            return web.json_response({"status": "success", "list": players, "tab": "players"})
    except Exception: return web.json_response({"error": "Server error"}, status=500)


# ==========================================
# АДМИНКА (КНОПКИ В КАНАЛЕ ВЫПЛАТ)
# ==========================================
@dp.callback_query(F.data.startswith("pay_"))
async def admin_pay(callback: types.CallbackQuery):
    await callback.message.edit_text(callback.message.text + "\n\n✅ **СТАТУС: ВЫПЛАЧЕНО**")
    await callback.answer("Успешно!")

@dp.callback_query(F.data.startswith("reject_"))
async def admin_reject(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    u_id = int(parts[1]); amount = int(parts[2])
    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE users SET bonus_balance = bonus_balance + $1 WHERE user_id = $2", amount, u_id)
    await callback.message.edit_text(callback.message.text + "\n\n❌ **СТАТУС: ОТКЛОНЕНО (Баланс возвращен)**")
    await callback.answer("Баланс возвращен игроку!")

# ==========================================
# БОТ
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    current_time = time.time()
    ref_id = None
    
    if command.args and command.args.startswith("ref_"):
        r_id = command.args.split("_")[1]
        if r_id.isdigit() and int(r_id) != user_id: ref_id = int(r_id)

    async with db_pool.acquire() as conn:
        user_data = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        if not user_data:
            await conn.execute("INSERT INTO users (user_id, referrer_id, first_name) VALUES ($1, $2, $3)", user_id, ref_id, first_name)
            if ref_id:
                try: await bot.send_message(ref_id, "🎉 <b>Новый друг по твоей ссылке!</b>", parse_mode="HTML")
                except Exception: pass

    if await check_subscription(user_id, CHANNEL_RU) or await check_subscription(user_id, CHANNEL_SNG):
        custom_url = f"{WEB_APP_URL}?v={int(current_time)}"
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🎮 ИГРАТЬ (Tap to Earn)", web_app=WebAppInfo(url=custom_url)))
        await message.answer_photo(photo=BANNER_GAME, caption=f"🚀 <b>С возвращением, {first_name}!</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🇷🇺 Канал (РФ)", url=f"https://t.me/{CHANNEL_RU[1:]}"))
        builder.row(types.InlineKeyboardButton(text="🌍 Канал (СНГ/Другие)", url=f"https://t.me/{CHANNEL_SNG[1:]}"))
        builder.row(types.InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub"))
        await message.answer_photo(photo=BANNER_GAME, caption=f"👋 <b>Привет, {first_name}!</b>\n\n🔒 Подпишись для доступа:", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "check_sub")
async def process_check(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if await check_subscription(user_id, CHANNEL_RU) or await check_subscription(user_id, CHANNEL_SNG):
        custom_url = f"{WEB_APP_URL}?v={int(time.time())}"
        game_builder = InlineKeyboardBuilder()
        game_builder.row(types.InlineKeyboardButton(text="🎮 ИГРАТЬ (Tap to Earn)", web_app=WebAppInfo(url=custom_url)))
        await callback.message.delete()
        await bot.send_photo(chat_id=callback.message.chat.id, photo=BANNER_GAME, caption="✅ <b>Отлично!</b>", reply_markup=game_builder.as_markup(), parse_mode="HTML")
    else:
        await callback.answer("❌ Ты еще не подписался!", show_alert=True)

async def main():
    await init_db()
    print("Бот запущен! Включен античит и защита БД.")
    app = web.Application()
    import aiohttp_cors
    cors = aiohttp_cors.setup(app, defaults={"*": aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*")})
    
    cors.add(app.router.add_post('/api/sync', sync_api))
    cors.add(app.router.add_post('/api/buy', buy_api))
    cors.add(app.router.add_post('/api/daily-claim', daily_claim_api))
    cors.add(app.router.add_post('/api/claim-sponsor', claim_sponsor_api))
    cors.add(app.router.add_post('/api/claim-daily-quest', claim_daily_quest_api))
    cors.add(app.router.add_post('/api/leaderboard', leaderboard_api))
    cors.add(app.router.add_post('/api/turbine-claim', turbine_claim_api))
    cors.add(app.router.add_post('/api/pvp-result', pvp_result_api))
    cors.add(app.router.add_post('/api/withdraw', withdraw_api))
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    await web.TCPSite(runner, '0.0.0.0', port).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())