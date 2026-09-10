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

YOUR_TELEGRAM_ID = None  
CHANNEL_RU = "@robuxtap_ru"
CHANNEL_SNG = "@robuxtap_sng"
WEB_APP_URL = "https://grubot.vercel.app/"

SPONSOR_CHANNELS = {
    1: "@grusponsors",
    2: "@grulvl",
    3: "@grufans",
    4: "@gruroom"
}

BANNER_WELCOME = "https://images.unsplash.com/photo-1614680376573-df3480f0c6ff?q=80&w=1000&auto=format&fit=crop"
BANNER_GAME = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1000&auto=format&fit=crop"    

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db_pool = None 

ROOM_LEVELS = {
    1: {'cost': 15000, 'income': 3},
    2: {'cost': 500000, 'income': 6},
    3: {'cost': 1500000, 'income': 12}
}

ARTIFACT_COSTS = {
    'pepe': 50000, 
    'spotty': 250000, 
    'durov_cap': 1000000
}

ARENA_THEMES_COSTS = {
    'crypto': 1000000,
    'cyber': 5000000
}

TEXTS = {
    'ru': {
        'welcome': "👋 <b>Привет, {name}!</b>\n\n🔒 Подпишись на наши каналы для доступа к игре:",
        'welcome_back': "🚀 <b>С возвращением, {name}!</b>",
        'play_btn': "🎮 ИГРАТЬ (Tap to Earn)",
        'sub_ru': "🇷🇺 Канал (РФ)",
        'sub_sng': "🌍 Канал (СНГ/Другие)",
        'check_sub': "✅ Я подписался",
        'not_subbed': "❌ Ты еще не подписался на каналы!",
        'good': "✅ <b>Отлично! Доступ открыт.</b>",
        'new_ref': "🎉 <b>Новый друг присоединился по твоей ссылке!</b>"
    },
    'en': {
        'welcome': "👋 <b>Hello, {name}!</b>\n\n🔒 Subscribe to our channels to get access:",
        'welcome_back': "🚀 <b>Welcome back, {name}!</b>",
        'play_btn': "🎮 PLAY (Tap to Earn)",
        'sub_ru': "🇷🇺 Channel (RU)",
        'sub_sng': "🌍 Channel (Global)",
        'check_sub': "✅ I subscribed",
        'not_subbed': "❌ You haven't subscribed yet!",
        'good': "✅ <b>Awesome! Access granted.</b>",
        'new_ref': "🎉 <b>A new friend joined via your link!</b>"
    }
}

async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, statement_cache_size=0)
    
    async with db_pool.acquire() as conn:
        await conn.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            referrer_id BIGINT,
            first_name TEXT DEFAULT 'Игрок',
            username TEXT DEFAULT '',
            squad_id TEXT DEFAULT '',
            taps_balance BIGINT DEFAULT 0,
            bonus_balance BIGINT DEFAULT 0,
            multitap_level INTEGER DEFAULT 1,
            bot_level INTEGER DEFAULT 0,
            max_energy_level INTEGER DEFAULT 1,
            current_room_level INTEGER DEFAULT 0,
            owned_skins TEXT DEFAULT '["default"]',
            current_skin TEXT DEFAULT 'default',
            last_sync_time DOUBLE PRECISION DEFAULT 0,
            last_squad_join_time DOUBLE PRECISION DEFAULT 0,
            rockets_count INTEGER DEFAULT 3,
            rocket_expires_at DOUBLE PRECISION DEFAULT 0,
            last_play_date TEXT DEFAULT '',
            daily_streak INTEGER DEFAULT 0,
            last_claim_date TEXT DEFAULT '',
            claimed_sponsors TEXT DEFAULT '[]',
            daily_taps BIGINT DEFAULT 0,
            daily_quest_claimed INTEGER DEFAULT 0
        )''')
        
        try: await conn.execute("ALTER TABLE users ADD COLUMN language TEXT")
        except asyncpg.exceptions.DuplicateColumnError: pass
        try: await conn.execute("ALTER TABLE users ADD COLUMN turbine_charges INTEGER")
        except asyncpg.exceptions.DuplicateColumnError: pass
        try: await conn.execute("ALTER TABLE users ADD COLUMN last_turbine_date TEXT DEFAULT ''")
        except asyncpg.exceptions.DuplicateColumnError: pass
        try: await conn.execute("ALTER TABLE users ADD COLUMN owned_arena_themes TEXT DEFAULT '[\"meme\"]'")
        except asyncpg.exceptions.DuplicateColumnError: pass

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
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
            
        user_id = user_data.get("id")
        is_premium = user_data.get("is_premium", False)
        
        # ЛИМИТЫ (Premium vs Обычный)
        max_turbine_charges = 2 if is_premium else 1
        max_rockets = 3 if is_premium else 2

        standard_clicks = data.get("standard_clicks", 0)
        rocket_clicks = data.get("rocket_clicks", 0)
        first_name = user_data.get("first_name", "Игрок")
        username = user_data.get("username", "")
        current_time = time.time()
        current_date = time.strftime('%Y-%m-%d')
        
        async with db_pool.acquire() as conn:
            user_db = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
            if not user_db: return web.json_response({"error": "User not found"}, status=404)
            
            rockets_count = user_db['rockets_count']
            last_play_date = user_db['last_play_date']
            daily_taps = user_db['daily_taps']
            daily_quest_claimed = user_db['daily_quest_claimed']
            
            turbine_charges = user_db.get('turbine_charges')
            if turbine_charges is None: turbine_charges = max_turbine_charges
            last_turbine_date = user_db.get('last_turbine_date', '')

            if last_play_date != current_date:
                rockets_count = max_rockets
                last_play_date = current_date
                daily_taps = 0
                daily_quest_claimed = 0

            if last_turbine_date != current_date:
                turbine_charges = max_turbine_charges
                last_turbine_date = current_date

            total_clicks_claimed = standard_clicks + rocket_clicks
            elapsed_sec = current_time - user_db['last_sync_time'] if user_db['last_sync_time'] > 0 else 0
            MAX_CLICKS_PER_SEC = 30
            safe_time = max(elapsed_sec, 3.0)
            max_possible_clicks = int(MAX_CLICKS_PER_SEC * safe_time)
            
            valid_total_clicks = min(total_clicks_claimed, max_possible_clicks)
            
            if total_clicks_claimed > 0:
                ratio = valid_total_clicks / total_clicks_claimed
                valid_standard = int(standard_clicks * ratio); valid_rocket = int(rocket_clicks * ratio)
            else:
                valid_standard, valid_rocket = 0, 0

            earned_from_taps = valid_standard * user_db['multitap_level']
            if current_time <= user_db['rocket_expires_at'] + 8.0:
                earned_from_taps += valid_rocket * user_db['multitap_level'] * 5
            else:
                earned_from_taps += valid_rocket * user_db['multitap_level']
                
            daily_taps += earned_from_taps
            
            earned_passive = 0; is_offline_reward = False
            studio_income = ROOM_LEVELS.get(user_db['current_room_level'], {}).get('income', 0)
            
            if user_db['last_sync_time'] > 0 and elapsed_sec > 0:
                if elapsed_sec < 60: earned_passive = int(elapsed_sec * studio_income)
                else:
                    if user_db['bot_level'] > 0:
                        active_offline_sec = min(elapsed_sec, 10800)
                        earned_passive = int(active_offline_sec * (studio_income + user_db['bot_level']))
                        is_offline_reward = True
            
            new_taps_bal = user_db['taps_balance'] + earned_from_taps
            new_bonus_bal = user_db['bonus_balance'] + earned_passive
            
            await conn.execute('''UPDATE users 
                              SET taps_balance = $1, bonus_balance = $2, last_sync_time = $3, first_name = $4, username = $5, 
                                  rockets_count = $6, last_play_date = $7, daily_taps = $8, daily_quest_claimed = $9,
                                  turbine_charges = $10, last_turbine_date = $11
                              WHERE user_id = $12''', 
                           new_taps_bal, new_bonus_bal, current_time, first_name, username, rockets_count, last_play_date, daily_taps, daily_quest_claimed, turbine_charges, last_turbine_date, user_id)
            
            try: owned_themes = json.loads(user_db['owned_arena_themes'] or '["meme"]')
            except Exception: owned_themes = ["meme"]

        return web.json_response({
            "status": "success", "new_taps_balance": new_taps_bal, "new_bonus_balance": new_bonus_bal,
            "earned_offline": earned_passive if is_offline_reward else 0, "current_squad": user_db['squad_id'], 
            "rockets_left": rockets_count, "max_rockets": max_rockets, "daily_streak": user_db['daily_streak'], "last_claim_date": user_db['last_claim_date'],
            "claimed_sponsors": user_db['claimed_sponsors'], "daily_taps": daily_taps, "daily_quest_claimed": daily_quest_claimed,
            "turbine_charges": turbine_charges, "max_charges": max_turbine_charges,
            "owned_arena_themes": owned_themes
        })
    except Exception as e: return web.json_response({"error": f"Server error"}, status=500)

async def turbine_claim_api(request):
    try:
        data = await request.json()
        user_data = validate_telegram_data(data.get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        
        user_id = user_data.get("id")
        earned = int(data.get("amount", 0))
        is_premium = user_data.get("is_premium", False)
        max_charges = 2 if is_premium else 1
        current_date = time.strftime('%Y-%m-%d')
        
        # АНТИЧИТ: Реалистичный лимит для Турбины (за 10 секунд физически не выжать больше 30 000)
        if earned < 0 or earned > 30000:
            return web.json_response({"error": "Превышен лимит добычи!"}, status=400)

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT turbine_charges, last_turbine_date, bonus_balance FROM users WHERE user_id = $1", user_id)
            if not row: return web.json_response({"error": "User not found"}, status=404)
            
            charges = row['turbine_charges'] if row['turbine_charges'] is not None else max_charges
            last_date = row['last_turbine_date']
            
            if last_date != current_date:
                charges = max_charges
                last_date = current_date
                
            if charges <= 0:
                return web.json_response({"error": "Заряды турбины исчерпаны!"}, status=400)
                
            new_charges = charges - 1
            new_bonus = row['bonus_balance'] + earned
            
            await conn.execute("UPDATE users SET turbine_charges = $1, last_turbine_date = $2, bonus_balance = $3 WHERE user_id = $4", 
                               new_charges, last_date, new_bonus, user_id)
            
            return web.json_response({"status": "success", "new_bonus_balance": new_bonus, "turbine_charges": new_charges, "max_charges": max_charges})
    except Exception as e: return web.json_response({"error": str(e)}, status=500)

async def pvp_result_api(request):
    try:
        data = await request.json()
        user_data = validate_telegram_data(data.get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        
        user_id = user_data.get("id")
        bet = int(data.get("bet", 0))
        is_win = data.get("is_win", False)
        
        # АНТИЧИТ: Проверка минимальной ставки
        if bet < 100: return web.json_response({"error": "Минимальная ставка 100 $ROB!"}, status=400)

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT taps_balance, bonus_balance FROM users WHERE user_id = $1", user_id)
            if not row: return web.json_response({"error": "User not found"}, status=404)
            
            taps_bal = row['taps_balance']
            bonus_bal = row['bonus_balance']
            total_bal = taps_bal + bonus_bal
            
            # АНТИЧИТ: Проверка баланса игрока
            if total_bal < bet:
                return web.json_response({"error": "Недостаточно средств!"}, status=400)
                
            if is_win:
                profit = int(bet * 0.95)
                new_bonus = bonus_bal + profit
                new_taps = taps_bal
            else:
                loss = bet
                if bonus_bal >= loss:
                    new_bonus = bonus_bal - loss
                    new_taps = taps_bal
                else:
                    remainder = loss - bonus_bal
                    new_bonus = 0
                    new_taps = taps_bal - remainder
                    
            await conn.execute("UPDATE users SET taps_balance = $1, bonus_balance = $2 WHERE user_id = $3", new_taps, new_bonus, user_id)
            return web.json_response({"status": "success", "new_taps_balance": new_taps, "new_bonus_balance": new_bonus})
    except Exception as e: return web.json_response({"error": str(e)}, status=500)

async def buy_api(request):
    try:
        data = await request.json()
        user_data = validate_telegram_data(data.get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        user_id = user_data.get("id"); buy_type = data.get("type") 
        async with db_pool.acquire() as conn:
            user_db = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
            taps_bal = int(user_db['taps_balance'] or 0); bonus_bal = int(user_db['bonus_balance'] or 0)
            total_balance = taps_bal + bonus_bal; cost = 0; column_to_update = ""; new_value = 0
            
            if buy_type == "tech":
                item_id = data.get("item_id")
                if item_id == "multitap": cost = get_upgrade_cost(2000, int(user_db['multitap_level'] or 1)); column_to_update = "multitap_level"; new_value = int(user_db['multitap_level'] or 1) + 1
                elif item_id == "energy": cost = get_upgrade_cost(2000, int(user_db['max_energy_level'] or 1)); column_to_update = "max_energy_level"; new_value = int(user_db['max_energy_level'] or 1) + 1
                elif item_id == "bot": cost = get_upgrade_cost(5000, int(user_db['bot_level'] or 0)); column_to_update = "bot_level"; new_value = int(user_db['bot_level'] or 0) + 1
            
            elif buy_type == "skin":
                item_id = data.get("item_id")
                cost = ARTIFACT_COSTS.get(item_id, 0) 
                owned_skins = json.loads(user_db['owned_skins'] or '[]')
                if item_id in owned_skins: return web.json_response({"error": "Уже куплено"}, status=400)
                owned_skins.append(item_id); column_to_update = "owned_skins"; new_value = json.dumps(owned_skins)
            
            elif buy_type == "room_upgrade":
                level_id = data.get("level"); cost = ROOM_LEVELS[level_id]['cost']; column_to_update = "current_room_level"; new_value = level_id

            elif buy_type == "arena_theme":
                item_id = data.get("item_id")
                cost = ARENA_THEMES_COSTS.get(item_id, 0)
                try: owned_themes = json.loads(user_db['owned_arena_themes'] or '["meme"]')
                except Exception: owned_themes = ["meme"]
                
                if item_id in owned_themes: return web.json_response({"error": "Уже куплено"}, status=400)
                owned_themes.append(item_id)
                column_to_update = "owned_arena_themes"
                new_value = json.dumps(owned_themes)
            
            if cost > 0 and total_balance < cost: return web.json_response({"error": "Недостаточно средств"}, status=400)
            if bonus_bal >= cost: new_bonus_bal = bonus_bal - cost; new_taps_bal = taps_bal
            else: remainder = cost - bonus_bal; new_bonus_bal = 0; new_taps_bal = taps_bal - remainder
            
            if column_to_update: await conn.execute(f'UPDATE users SET taps_balance = $1, bonus_balance = $2, {column_to_update} = $3 WHERE user_id = $4', new_taps_bal, new_bonus_bal, new_value, user_id)
            return web.json_response({"status": "success", "new_taps_balance": new_taps_bal, "new_bonus_balance": new_bonus_bal})
    except Exception as e: return web.json_response({"error": str(e)}, status=500)

async def claim_daily_quest_api(request):
    try:
        user_data = validate_telegram_data((await request.json()).get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        user_id = user_data.get("id")
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT daily_taps, daily_quest_claimed, bonus_balance FROM users WHERE user_id = $1", user_id)
            if not row: return web.json_response({"error": "User not found"}, status=404)
            if row['daily_taps'] < 5000: return web.json_response({"error": "Цель еще не выполнена!"}, status=400)
            if row['daily_quest_claimed'] == 1: return web.json_response({"error": "Награда уже получена!"}, status=400)
            new_bonus = row['bonus_balance'] + 10000
            await conn.execute("UPDATE users SET daily_quest_claimed = 1, bonus_balance = $1 WHERE user_id = $2", new_bonus, user_id)
            return web.json_response({"status": "success", "new_bonus_balance": new_bonus})
    except Exception as e: return web.json_response({"error": str(e)}, status=500)

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
            reward = streak * 100; new_bonus = int(row['bonus_balance'] or 0) + reward
            await conn.execute("UPDATE users SET daily_streak = $1, last_claim_date = $2, bonus_balance = $3 WHERE user_id = $4", streak, today_str, new_bonus, user_id)
            return web.json_response({"status": "success", "daily_streak": streak, "last_claim_date": today_str, "new_bonus_balance": new_bonus, "reward_received": reward})
    except Exception as e: return web.json_response({"error": str(e)}, status=500)

async def claim_sponsor_api(request):
    try:
        data = await request.json()
        user_data = validate_telegram_data(data.get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        user_id = user_data.get("id"); sponsor_id = int(data.get("sponsor_id", 0))
        channel = SPONSOR_CHANNELS.get(sponsor_id)
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT claimed_sponsors, bonus_balance FROM users WHERE user_id = $1", user_id)
            claimed = json.loads(row['claimed_sponsors'] or '[]'); new_bonus = int(row['bonus_balance'] or 0) + 450
            if sponsor_id in claimed: return web.json_response({"error": "Награда уже получена!"}, status=400)
            if not await check_subscription(user_id, channel): return web.json_response({"error": f"Вы не подписаны!"}, status=400)
            claimed.append(sponsor_id)
            await conn.execute("UPDATE users SET claimed_sponsors = $1, bonus_balance = $2 WHERE user_id = $3", json.dumps(claimed), new_bonus, user_id)
            return web.json_response({"status": "success", "claimed_sponsors": json.dumps(claimed), "new_bonus_balance": new_bonus})
    except Exception as e: return web.json_response({"error": str(e)}, status=500)

async def activate_rocket_api(request):
    try:
        user_data = validate_telegram_data((await request.json()).get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        user_id = user_data.get("id"); current_time = time.time(); current_date = time.strftime('%Y-%m-%d')
        is_premium = user_data.get("is_premium", False)
        max_rockets = 3 if is_premium else 2

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT rockets_count, rocket_expires_at, last_play_date FROM users WHERE user_id = $1", user_id)
            r_count = int(row['rockets_count']) if row['rockets_count'] is not None else max_rockets
            r_exp = float(row['rocket_expires_at']) if row['rocket_expires_at'] is not None else 0
            last_date = row['last_play_date']
            
            if last_date != current_date: r_count = max_rockets; last_date = current_date
            if r_count <= 0: return web.json_response({"error": "Ракеты закончились!"}, status=400)
            if current_time <= r_exp: return web.json_response({"error": "Ракета уже активна!"}, status=400)
            new_count = r_count - 1; new_exp = current_time + 15
            await conn.execute("UPDATE users SET rockets_count = $1, rocket_expires_at = $2, last_play_date = $3 WHERE user_id = $4", new_count, new_exp, last_date, user_id)
            return web.json_response({"status": "success", "rockets_left": new_count})
    except Exception as e: return web.json_response({"error": str(e)}, status=500)

async def create_squad_api(request):
    try:
        data = await request.json()
        user_data = validate_telegram_data(data.get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        channel_username = data.get("channel", "").strip(); user_id = user_data.get("id")
        if not channel_username.startswith("@"): channel_username = "@" + channel_username
        try:
            member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
            if member.status not in ["administrator", "creator"]: return web.json_response({"error": "Вы не админ!"}, status=400)
        except Exception: return web.json_response({"error": "Добавьте бота в канал!"}, status=400)
        return web.json_response({"status": "success", "link": f"https://t.me/grutap_robot?start=squad_{channel_username[1:]}"})
    except Exception: return web.json_response({"error": "Ошибка"}, status=500)

async def leaderboard_api(request):
    try:
        data = await request.json(); tab = data.get("tab", "players")
        user_data = validate_telegram_data(data.get("initData"), BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        req_user_id = user_data.get("id")
        async with db_pool.acquire() as conn:
            if tab == "players":
                rows = await conn.fetch('SELECT user_id, first_name, username, (taps_balance + bonus_balance) as score FROM users ORDER BY score DESC LIMIT 50')
                players = [{"id": r['user_id'], "name": r['first_name'] or "Аноним", "username": r['username'], "score": r['score'], "isMe": r['user_id'] == req_user_id} for r in rows]
                return web.json_response({"status": "success", "list": players, "tab": "players"})
            
            elif tab == "squads":
                # ИСПРАВЛЕН БАГ ЛИДЕРБОРДА (Устранен конфликт переменных)
                rows = await conn.fetch("SELECT squad_id, COUNT(user_id) as members, SUM(taps_balance + bonus_balance) as ts FROM users WHERE squad_id != '' GROUP BY squad_id ORDER BY ts DESC LIMIT 50")
                user_row = await conn.fetchrow("SELECT squad_id FROM users WHERE user_id = $1", req_user_id) 
                user_squad_id = user_row['squad_id'] if user_row else ""
                
                squads = [{"id": row_data['squad_id'], "members": row_data['members'], "score": row_data['ts'], "isMySquad": row_data['squad_id'] == user_squad_id} for row_data in rows]
                return web.json_response({"status": "success", "list": squads, "tab": "squads"})
    except Exception: return web.json_response({"error": "Server error"}, status=500)


# ==========================================
# ЛОГИКА БОТА И МУЛЬТИЯЗЫЧНОСТЬ
# ==========================================

async def send_main_menu(message_or_callback, user_id, first_name, lang):
    t = TEXTS.get(lang, TEXTS['ru'])
    
    async with db_pool.acquire() as conn:
        r = await conn.fetchrow("SELECT COUNT(*) as count FROM users WHERE referrer_id = $1", user_id)
        refs_count = r['count'] if r else 0

    if await check_subscription(user_id, CHANNEL_RU) or await check_subscription(user_id, CHANNEL_SNG):
        custom_url = f"{WEB_APP_URL}?refs={refs_count}&v={int(time.time())}&lang={lang}"
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text=t['play_btn'], web_app=WebAppInfo(url=custom_url)))
        
        if isinstance(message_or_callback, types.Message):
            await message_or_callback.answer_photo(photo=BANNER_GAME, caption=t['welcome_back'].format(name=first_name), reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message_or_callback.message.delete()
            await bot.send_photo(chat_id=message_or_callback.message.chat.id, photo=BANNER_GAME, caption=t['good'], reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text=t['sub_ru'], url=f"https://t.me/{CHANNEL_RU[1:]}"))
        builder.row(types.InlineKeyboardButton(text=t['sub_sng'], url=f"https://t.me/{CHANNEL_SNG[1:]}"))
        builder.row(types.InlineKeyboardButton(text=t['check_sub'], callback_data="check_sub"))
        
        if isinstance(message_or_callback, types.Message):
            await message_or_callback.answer_photo(photo=BANNER_WELCOME, caption=t['welcome'].format(name=first_name), reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message_or_callback.answer(t['not_subbed'], show_alert=True)

@dp.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    current_time = time.time()
    ref_id, squad_id = None, ""
    
    if command.args:
        if command.args.startswith("ref_"):
            r_id = command.args.split("_")[1]
            if r_id.isdigit() and int(r_id) != user_id: ref_id = int(r_id)
        elif command.args.startswith("squad_"): squad_id = "@" + command.args.split("_")[1]

    async with db_pool.acquire() as conn:
        user_data = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        
        if not user_data:
            await conn.execute("INSERT INTO users (user_id, referrer_id, first_name, squad_id, last_squad_join_time) VALUES ($1, $2, $3, $4, $5)", user_id, ref_id, first_name, squad_id, current_time if squad_id else 0)
            if ref_id:
                try: 
                    ref_data = await conn.fetchrow("SELECT language FROM users WHERE user_id = $1", ref_id)
                    ref_lang = ref_data['language'] if ref_data and ref_data['language'] else 'ru'
                    await bot.send_message(ref_id, TEXTS[ref_lang]['new_ref'], parse_mode="HTML")
                except Exception: pass
                
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru"),
                        types.InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang_en"))
            await message.answer("🌍 Выберите язык / Choose your language:", reply_markup=builder.as_markup())
            return
            
        else:
            if squad_id and user_data['squad_id'] != squad_id:
                if current_time - user_data['last_squad_join_time'] >= 604800 or user_data['last_squad_join_time'] == 0:
                    await conn.execute("UPDATE users SET squad_id = $1, last_squad_join_time = $2 WHERE user_id = $3", squad_id, current_time, user_id)

            lang = user_data['language']
            if not lang:
                builder = InlineKeyboardBuilder()
                builder.row(types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang_ru"),
                            types.InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang_en"))
                await message.answer("🌍 Выберите язык / Choose your language:", reply_markup=builder.as_markup())
                return

    await send_main_menu(message, user_id, first_name, lang)

@dp.callback_query(F.data.startswith("setlang_"))
async def process_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    async with db_pool.acquire() as conn:
        await conn.execute("UPDATE users SET language = $1 WHERE user_id = $2", lang, user_id)
    await callback.message.delete()
    await send_main_menu(callback.message, user_id, callback.from_user.first_name, lang)

@dp.callback_query(F.data == "check_sub")
async def process_check(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    async with db_pool.acquire() as conn:
        user_data = await conn.fetchrow("SELECT language FROM users WHERE user_id = $1", user_id)
        lang = user_data['language'] if user_data and user_data['language'] else 'ru'
    await send_main_menu(callback, user_id, callback.from_user.first_name, lang)

async def main():
    await init_db()
    print("Бот запущен! Магазин СТИЛЕЙ АРЕНЫ активирован.")
    app = web.Application()
    import aiohttp_cors
    cors = aiohttp_cors.setup(app, defaults={"*": aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*")})
    
    cors.add(app.router.add_post('/api/sync', sync_api))
    cors.add(app.router.add_post('/api/buy', buy_api))
    cors.add(app.router.add_post('/api/activate-rocket', activate_rocket_api))
    cors.add(app.router.add_post('/api/daily-claim', daily_claim_api))
    cors.add(app.router.add_post('/api/claim-sponsor', claim_sponsor_api))
    cors.add(app.router.add_post('/api/claim-daily-quest', claim_daily_quest_api))
    cors.add(app.router.add_post('/api/create-squad', create_squad_api))
    cors.add(app.router.add_post('/api/leaderboard', leaderboard_api))
    cors.add(app.router.add_post('/api/turbine-claim', turbine_claim_api))
    cors.add(app.router.add_post('/api/pvp-result', pvp_result_api))
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    await web.TCPSite(runner, '0.0.0.0', port).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())