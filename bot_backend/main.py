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
import aiosqlite
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

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
DB_NAME = 'database.db'

ROOM_LEVELS = {
    1: {'cost': 15000, 'income': 3},
    2: {'cost': 500000, 'income': 6},
    3: {'cost': 1500000, 'income': 12}
}

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
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
            last_squad_join_time REAL DEFAULT 0,
            rockets_count INTEGER DEFAULT 3,
            rocket_expires_at REAL DEFAULT 0,
            last_play_date TEXT DEFAULT '',
            daily_streak INTEGER DEFAULT 0,
            last_claim_date TEXT DEFAULT '',
            claimed_sponsors TEXT DEFAULT '[]',
            daily_taps INTEGER DEFAULT 0,
            daily_quest_claimed INTEGER DEFAULT 0
        )''')
        await db.commit()

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

SKIN_COSTS = {'coin': 50000, 'diamond': 250000, 'crown': 1000000}

async def sync_api(request):
    try:
        data = await request.json()
        init_data = data.get("initData")
        standard_clicks = data.get("standard_clicks", 0)
        rocket_clicks = data.get("rocket_clicks", 0)
        
        user_data = validate_telegram_data(init_data, BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
            
        user_id = user_data.get("id")
        first_name = user_data.get("first_name", "Игрок")
        username = user_data.get("username", "")
        current_time = time.time()
        current_date = time.strftime('%Y-%m-%d')
        
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                user_db = await cursor.fetchone()
                
            if not user_db: return web.json_response({"error": "User not found"}, status=404)
            
            rockets_count = user_db['rockets_count']
            last_play_date = user_db['last_play_date']
            daily_taps = user_db['daily_taps']
            daily_quest_claimed = user_db['daily_quest_claimed']
            
            if last_play_date != current_date:
                rockets_count = 3
                last_play_date = current_date
                daily_taps = 0
                daily_quest_claimed = 0

            # АНТИЧИТ НА ОБЩЕЕ КОЛИЧЕСТВО КЛИКОВ
            total_clicks_claimed = standard_clicks + rocket_clicks
            elapsed_sec = current_time - user_db['last_sync_time'] if user_db['last_sync_time'] > 0 else 0
            MAX_CLICKS_PER_SEC = 30
            safe_time = max(elapsed_sec, 3.0)
            max_possible_clicks = int(MAX_CLICKS_PER_SEC * safe_time)
            
            valid_total_clicks = min(total_clicks_claimed, max_possible_clicks)
            
            # Если игрок превысил лимит, урезаем пропорционально
            if total_clicks_claimed > 0:
                ratio = valid_total_clicks / total_clicks_claimed
                valid_standard = int(standard_clicks * ratio)
                valid_rocket = int(rocket_clicks * ratio)
            else:
                valid_standard, valid_rocket = 0, 0

            # РАСЧЕТ ДОХОДА С 3-СЕКУНДНЫМ GRACE PERIOD ДЛЯ РАКЕТЫ
            earned_from_taps = valid_standard * user_db['multitap_level']
            
            if current_time <= user_db['rocket_expires_at'] + 3.0: # +3 секунды на пинг
                earned_from_taps += valid_rocket * user_db['multitap_level'] * 5
            else:
                # Если пытаются прислать ракетные клики когда ракета давно кончилась, считаем как обычные
                earned_from_taps += valid_rocket * user_db['multitap_level']
                
            daily_taps += earned_from_taps
            
            # ПАССИВНЫЙ ДОХОД
            earned_passive = 0
            is_offline_reward = False
            studio_income = ROOM_LEVELS.get(user_db['current_room_level'], {}).get('income', 0)
            
            if user_db['last_sync_time'] > 0 and elapsed_sec > 0:
                if elapsed_sec < 60:
                    earned_passive = int(elapsed_sec * studio_income)
                else:
                    if user_db['bot_level'] > 0:
                        active_offline_sec = min(elapsed_sec, 10800)
                        earned_passive = int(active_offline_sec * (studio_income + user_db['bot_level']))
                        is_offline_reward = True
            
            new_taps_bal = user_db['taps_balance'] + earned_from_taps
            new_bonus_bal = user_db['bonus_balance'] + earned_passive
            
            await db.execute('''UPDATE users 
                              SET taps_balance = ?, bonus_balance = ?, last_sync_time = ?, first_name = ?, username = ?, 
                                  rockets_count = ?, last_play_date = ?, daily_taps = ?, daily_quest_claimed = ?
                              WHERE user_id = ?''', 
                           (new_taps_bal, new_bonus_bal, current_time, first_name, username, rockets_count, last_play_date, daily_taps, daily_quest_claimed, user_id))
            await db.commit()
            
        return web.json_response({
            "status": "success", 
            "new_taps_balance": new_taps_bal, 
            "new_bonus_balance": new_bonus_bal,
            "earned_offline": earned_passive if is_offline_reward else 0, 
            "current_squad": user_db['squad_id'], 
            "rockets_left": rockets_count,
            "daily_streak": user_db['daily_streak'],
            "last_claim_date": user_db['last_claim_date'],
            "claimed_sponsors": user_db['claimed_sponsors'],
            "daily_taps": daily_taps,
            "daily_quest_claimed": daily_quest_claimed
        })
    except Exception as e:
        print(f"Sync error: {e}")
        return web.json_response({"error": f"Server error: {str(e)}"}, status=500)

async def claim_daily_quest_api(request):
    try:
        data = await request.json()
        init_data = data.get("initData")
        user_data = validate_telegram_data(init_data, BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        
        user_id = user_data.get("id")
        
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT daily_taps, daily_quest_claimed, bonus_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
            
            if not row: return web.json_response({"error": "User not found"}, status=404)
            
            if row['daily_taps'] < 5000: return web.json_response({"error": "Цель еще не выполнена!"}, status=400)
            if row['daily_quest_claimed'] == 1: return web.json_response({"error": "Награда уже получена!"}, status=400)
                
            new_bonus = row['bonus_balance'] + 10000
            
            await db.execute("UPDATE users SET daily_quest_claimed = 1, bonus_balance = ? WHERE user_id = ?", (new_bonus, user_id))
            await db.commit()
            
            return web.json_response({"status": "success", "new_bonus_balance": new_bonus})
    except Exception as e: return web.json_response({"error": str(e)}, status=500)

async def daily_claim_api(request):
    try:
        data = await request.json()
        init_data = data.get("initData")
        user_data = validate_telegram_data(init_data, BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        
        user_id = user_data.get("id")
        today_str = datetime.now().strftime('%Y-%m-%d')
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT daily_streak, last_claim_date, bonus_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
            if not row: return web.json_response({"error": "User not found"}, status=404)
            
            streak = int(row['daily_streak'] or 0)
            last_claim = row['last_claim_date']
            
            if last_claim == today_str: return web.json_response({"error": "Сегодня вы уже забрали награду!"}, status=400)
            if last_claim == yesterday_str: streak = (streak % 7) + 1
            else: streak = 1  
                
            reward = streak * 100
            new_bonus = int(row['bonus_balance'] or 0) + reward
            
            await db.execute("UPDATE users SET daily_streak = ?, last_claim_date = ?, bonus_balance = ? WHERE user_id = ?", (streak, today_str, new_bonus, user_id))
            await db.commit()
            return web.json_response({"status": "success", "daily_streak": streak, "last_claim_date": today_str, "new_bonus_balance": new_bonus, "reward_received": reward})
    except Exception as e: return web.json_response({"error": str(e)}, status=500)

async def claim_sponsor_api(request):
    try:
        data = await request.json()
        init_data = data.get("initData")
        sponsor_id = int(data.get("sponsor_id", 0))
        
        user_data = validate_telegram_data(init_data, BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        
        user_id = user_data.get("id")
        channel = SPONSOR_CHANNELS.get(sponsor_id)
        if not channel: return web.json_response({"error": "Неверный ID спонсора"}, status=400)
        
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT claimed_sponsors, bonus_balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
            
            claimed = json.loads(row['claimed_sponsors'] or '[]')
            if sponsor_id in claimed: return web.json_response({"error": "Награда уже получена!"}, status=400)
            
            is_member = await check_subscription(user_id, channel)
            if not is_member: return web.json_response({"error": f"Вы не подписаны на канал {channel}!"}, status=400)
                
            claimed.append(sponsor_id)
            new_bonus = int(row['bonus_balance'] or 0) + 450
            
            await db.execute("UPDATE users SET claimed_sponsors = ?, bonus_balance = ? WHERE user_id = ?", (json.dumps(claimed), new_bonus, user_id))
            await db.commit()
            return web.json_response({"status": "success", "claimed_sponsors": json.dumps(claimed), "new_bonus_balance": new_bonus})
    except Exception as e: return web.json_response({"error": str(e)}, status=500)

async def activate_rocket_api(request):
    try:
        data = await request.json()
        init_data = data.get("initData")
        user_data = validate_telegram_data(init_data, BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        
        user_id = user_data.get("id")
        current_time = time.time()
        current_date = time.strftime('%Y-%m-%d')

        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT rockets_count, rocket_expires_at, last_play_date FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
            
            r_count = int(row[0]) if row[0] is not None else 3
            r_exp = float(row[1]) if row[1] is not None else 0
            last_date = row[2]
            
            if last_date != current_date:
                r_count = 3
                last_date = current_date

            if r_count <= 0: return web.json_response({"error": "Ракеты закончились!"}, status=400)
            if current_time <= r_exp: return web.json_response({"error": "Ракета уже активна!"}, status=400)

            new_count = r_count - 1
            new_exp = current_time + 15

            await db.execute("UPDATE users SET rockets_count = ?, rocket_expires_at = ?, last_play_date = ? WHERE user_id = ?", (new_count, new_exp, last_date, user_id))
            await db.commit()
            return web.json_response({"status": "success", "rockets_left": new_count})
    except Exception as e: return web.json_response({"error": str(e)}, status=500)

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
            
            taps_bal = int(user_db['taps_balance'] or 0)
            bonus_bal = int(user_db['bonus_balance'] or 0)
            total_balance = taps_bal + bonus_bal
            cost = 0; column_to_update = ""; new_value = 0
            
            if buy_type == "tech":
                item_id = data.get("item_id")
                if item_id == "multitap": 
                    cost = get_upgrade_cost(2000, int(user_db['multitap_level'] or 1))
                    column_to_update = "multitap_level"
                    new_value = int(user_db['multitap_level'] or 1) + 1
                elif item_id == "energy": 
                    cost = get_upgrade_cost(2000, int(user_db['max_energy_level'] or 1))
                    column_to_update = "max_energy_level"
                    new_value = int(user_db['max_energy_level'] or 1) + 1
                elif item_id == "bot": 
                    cost = get_upgrade_cost(5000, int(user_db['bot_level'] or 0))
                    column_to_update = "bot_level"
                    new_value = int(user_db['bot_level'] or 0) + 1
            elif buy_type == "skin":
                item_id = data.get("item_id")
                cost = SKIN_COSTS.get(item_id, 0)
                owned_skins = json.loads(user_db['owned_skins'] or '[]')
                if item_id in owned_skins: return web.json_response({"error": "Уже куплено"}, status=400)
                owned_skins.append(item_id); column_to_update = "owned_skins"; new_value = json.dumps(owned_skins)
            elif buy_type == "room_upgrade":
                level_id = data.get("level")
                if level_id not in ROOM_LEVELS: return web.json_response({"error": "Неверный уровень"}, status=400)
                if int(user_db['current_room_level'] or 0) >= level_id: return web.json_response({"error": "Уже куплено"}, status=400)
                cost = ROOM_LEVELS[level_id]['cost']; column_to_update = "current_room_level"; new_value = level_id
            
            if cost > 0 and total_balance < cost: return web.json_response({"error": "Недостаточно средств"}, status=400)
            if bonus_bal >= cost: new_bonus_bal = bonus_bal - cost; new_taps_bal = taps_bal
            else: remainder = cost - bonus_bal; new_bonus_bal = 0; new_taps_bal = taps_bal - remainder
                
            if column_to_update:
                await db.execute(f'UPDATE users SET taps_balance = ?, bonus_balance = ?, {column_to_update} = ? WHERE user_id = ?', (new_taps_bal, new_bonus_bal, new_value, user_id))
                await db.commit()
            
            return web.json_response({"status": "success", "new_taps_balance": new_taps_bal, "new_bonus_balance": new_bonus_bal})
    except Exception as e:
        print(f"Buy error: {e}")
        return web.json_response({"error": f"Server error: {str(e)}"}, status=500)

async def create_squad_api(request):
    try:
        data = await request.json()
        init_data = data.get("initData")
        channel_username = data.get("channel", "").strip()
        user_data = validate_telegram_data(init_data, BOT_TOKEN)
        if not user_data: return web.json_response({"error": "Unauthorized"}, status=401)
        user_id = user_data.get("id")
        if not channel_username.startswith("@"): channel_username = "@" + channel_username
        try:
            member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
            if member.status not in ["administrator", "creator"]: return web.json_response({"error": "Вы не админ!"}, status=400)
        except Exception: return web.json_response({"error": "Добавьте бота в канал!"}, status=400)
        link = f"https://t.me/grutap_robot?start=squad_{channel_username[1:]}"
        return web.json_response({"status": "success", "link": link})
    except Exception: return web.json_response({"error": "Ошибка"}, status=500)

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
                async with db.execute('SELECT user_id, first_name, username, (taps_balance + bonus_balance) as score FROM users ORDER BY score DESC LIMIT 50') as cursor: rows = await cursor.fetchall()
                players = [{"id": r[0], "name": r[1] or "Аноним", "username": r[2], "score": r[3], "isMe": r[0] == req_user_id} for r in rows]
                return web.json_response({"status": "success", "list": players, "tab": "players"})
            elif tab == "squads":
                async with db.execute("SELECT squad_id, COUNT(user_id), SUM(taps_balance + bonus_balance) as ts FROM users WHERE squad_id != '' GROUP BY squad_id ORDER BY ts DESC LIMIT 50") as cursor: rows = await cursor.fetchall()
                async with db.execute("SELECT squad_id FROM users WHERE user_id = ?", (req_user_id,)) as cursor: r = await cursor.fetchone(); us = r[0] if r else ""
                squads = [{"id": r[0], "members": r[1], "score": r[2], "isMySquad": r[0] == us} for r in rows]
                return web.json_response({"status": "success", "list": squads, "tab": "squads"})
    except Exception: return web.json_response({"error": "Server error"}, status=500)

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

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor: user_data = await cursor.fetchone()
        if not user_data:
            await db.execute("INSERT INTO users (user_id, referrer_id, first_name, squad_id, last_squad_join_time) VALUES (?, ?, ?, ?, ?)", (user_id, ref_id, first_name, squad_id, current_time if squad_id else 0))
            await db.commit()
            if ref_id:
                try: await bot.send_message(ref_id, "🎉 <b>Новый друг по ссылке!</b>", parse_mode="HTML")
                except Exception: pass
        else:
            if squad_id and user_data[4] != squad_id:
                if current_time - user_data[14] >= 604800 or user_data[14] == 0:
                    await db.execute("UPDATE users SET squad_id = ?, last_squad_join_time = ? WHERE user_id = ?", (squad_id, current_time, user_id))
                    await db.commit()

        async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,)) as cursor: refs_count = (await cursor.fetchone())[0]

    if await check_subscription(user_id, CHANNEL_RU) or await check_subscription(user_id, CHANNEL_SNG):
        custom_url = f"{WEB_APP_URL}?refs={refs_count}&v={int(current_time)}"
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🎮 ИГРАТЬ (Tap to Earn)", web_app=WebAppInfo(url=custom_url)))
        await message.answer_photo(photo=BANNER_GAME, caption=f"🚀 <b>С возвращением, {first_name}!</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
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
            async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,)) as cursor: refs_count = (await cursor.fetchone())[0]
        custom_url = f"{WEB_APP_URL}?refs={refs_count}&v={int(time.time())}"
        game_builder = InlineKeyboardBuilder()
        game_builder.row(types.InlineKeyboardButton(text="🎮 ИГРАТЬ (Tap to Earn)", web_app=WebAppInfo(url=custom_url)))
        await callback.message.delete()
        await bot.send_photo(chat_id=callback.message.chat.id, photo=BANNER_GAME, caption="✅ <b>Отлично!</b>", reply_markup=game_builder.as_markup(), parse_mode="HTML")
    else:
        await callback.answer("❌ Ты еще не подписался!", show_alert=True)

async def main():
    await init_db()
    print("Бот запущен!")
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
    
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    await web.TCPSite(runner, '0.0.0.0', port).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())