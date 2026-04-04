import logging
import sqlite3
import asyncio
import random
import os
from datetime import datetime, timedelta
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = os.getenv('BOT_TOKEN')

# Веб-сервер для UptimeRobot / Render
async def healthcheck(request):
    return web.Response(text="OK")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', healthcheck)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    print("✅ Веб-сервер запущен на порту 10000")

# ========== ВСЕ ТВОИ ЖК (более 100) ==========
buildings = {
    # Москва-Сити (20 очков)
    'neva_towers': {'name': 'Neva Towers', 'complex': 'Москва-Сити', 'points': 20, 'photo_path': 'photos/neva_towers.jpg'},
    'federation': {'name': 'Башня Федерация', 'complex': 'Москва-Сити', 'points': 20, 'photo_path': 'photos/federation.jpg'},
    'okyo': {'name': 'ЖК Око', 'complex': 'Москва-Сити', 'points': 20, 'photo_path': 'photos/okyo.jpg'},
    'mercury': {'name': 'Меркурий Сити Тауэр', 'complex': 'Москва-Сити', 'points': 20, 'photo_path': 'photos/mercury.jpg'},
    'capital_city': {'name': 'Город Столиц', 'complex': 'Москва-Сити', 'points': 20, 'photo_path': 'photos/capital_city.jpg'},
    'evolution': {'name': 'Башня Эволюция', 'complex': 'Москва-Сити', 'points': 20, 'photo_path': 'photos/evolution.jpg'},
    'imperia': {'name': 'Башня Империя', 'complex': 'Москва-Сити', 'points': 20, 'photo_path': 'photos/imperia.jpg'},
    
    # Москва (10 очков)
    'vysotsky': {'name': 'ЖК Высоцкий', 'complex': 'Екатеринбург', 'points': 10, 'photo_path': 'photos/vysotsky.jpg'},
    'lighthouse': {'name': 'ЖК Маяк', 'complex': 'Москва', 'points': 10, 'photo_path': 'photos/lighthouse.jpg'},
    'headliner': {'name': 'ЖК Хедлайнер', 'complex': 'Москва', 'points': 10, 'photo_path': 'photos/headliner.jpg'},
    'zilart': {'name': 'ЖК Зиларт', 'complex': 'Москва', 'points': 10, 'photo_path': 'photos/zilart.jpg'},
    'serdtse_stolicy': {'name': 'ЖК Сердце Столицы', 'complex': 'Москва', 'points': 10, 'photo_path': 'photos/serdtse_stolicy.jpg'},
    'alye_parusa': {'name': 'ЖК Алые Паруса', 'complex': 'Москва', 'points': 10, 'photo_path': 'photos/alye_parusa.jpg'},
    'vorobyovy_gory': {'name': 'ЖК Воробьёвы горы', 'complex': 'Москва', 'points': 10, 'photo_path': 'photos/vorobyovy_gory.jpg'},
    'triumph_palace': {'name': 'Триумф-Палас', 'complex': 'Москва', 'points': 10, 'photo_path': 'photos/triumph_palace.jpg'},
    'save_towers': {'name': 'Saving Towers', 'complex': 'Москва', 'points': 10, 'photo_path': 'photos/save_towers.jpg'},
    'presnya_city': {'name': 'Пресня Сити', 'complex': 'Москва', 'points': 10, 'photo_path': 'photos/presnya_city.jpg'},
    'kutuzovskaya_mile': {'name': 'Кутузовская Миля', 'complex': 'Москва', 'points': 10, 'photo_path': 'photos/kutuzovskaya_mile.jpg'},
    'dom_moskva': {'name': 'Дом на Мосфильмовской', 'complex': 'Москва', 'points': 10, 'photo_path': 'photos/dom_moskva.jpg'},
    'rublevo_arch': {'name': 'Рублево-Архангельское', 'complex': 'Москва', 'points': 10, 'photo_path': 'photos/rublevo_arch.jpg'},
    
    # Санкт-Петербург
    'lakhta_center': {'name': 'Лахта Центр', 'complex': 'Санкт-Петербург', 'points': 15, 'photo_path': 'photos/lakhta_center.jpg'},
    'ligov_city': {'name': 'Лигов Сити', 'complex': 'Санкт-Петербург', 'points': 10, 'photo_path': 'photos/ligov_city.jpg'},
    'neva_sky': {'name': 'Небоскреб Невский', 'complex': 'Санкт-Петербург', 'points': 10, 'photo_path': 'photos/neva_sky.jpg'},
    
    # Екатеринбург
    'vysotsky_ekb': {'name': 'Высоцкий', 'complex': 'Екатеринбург', 'points': 10, 'photo_path': 'photos/vysotsky_ekb.jpg'},
    'iset_tower': {'name': 'Isеt Tower', 'complex': 'Екатеринбург', 'points': 10, 'photo_path': 'photos/iset_tower.jpg'},
    
    # Казань
    'lazurnye_neba': {'name': 'Лазурные небеса', 'complex': 'Казань', 'points': 10, 'photo_path': 'photos/lazurnye_neba.jpg'},
    'kazan_river': {'name': 'Казань Ривер', 'complex': 'Казань', 'points': 10, 'photo_path': 'photos/kazan_river.jpg'},
    
    # Новосибирск
    'atlantic_city': {'name': 'Атлантик Сити', 'complex': 'Новосибирск', 'points': 10, 'photo_path': 'photos/atlantic_city.jpg'},
    'krasnaya_gorka': {'name': 'Красная горка', 'complex': 'Новосибирск', 'points': 10, 'photo_path': 'photos/krasnaya_gorka.jpg'},
}

# Добавляем до 100+ ЖК
for i in range(1, 81):
    buildings[f'building_{i}'] = {
        'name': f'ЖК "Столичный {i}"',
        'complex': f'Город {random.choice(["Москва", "СПб", "Казань", "Екатеринбург", "Новосибирск", "Краснодар", "Сочи", "Ростов-на-Дону"])}',
        'points': 10,
        'photo_path': f'photos/building_{i}.jpg'
    }

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def get_cooldown_hours(conquered_count):
    if conquered_count < 5:
        return 1.5
    elif conquered_count < 10:
        return 3
    elif conquered_count < 15:
        return 4
    elif conquered_count < 20:
        return 5
    else:
        return 6

def is_moscow_city(complex_name):
    return complex_name == 'Москва-Сити'

def check_prim(building):
    if is_moscow_city(building['complex']):
        return random.random() < 0.7
    else:
        return random.random() < 0.3

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect('roofer_game.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  first_name TEXT,
                  points INTEGER DEFAULT 0,
                  registered_date TEXT,
                  last_take_time TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS conquered_buildings
                 (user_id INTEGER,
                  building_id TEXT,
                  conquered_date TEXT,
                  points_earned INTEGER,
                  PRIMARY KEY (user_id, building_id))''')
    conn.commit()
    conn.close()

def register_user(user_id, username, first_name):
    conn = sqlite3.connect('roofer_game.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, username, first_name, points, registered_date, last_take_time) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_id, username, first_name, 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), None))
        conn.commit()
    conn.close()

def get_user_profile(user_id):
    conn = sqlite3.connect('roofer_game.db')
    c = conn.cursor()
    c.execute("SELECT points, first_name, last_take_time FROM users WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()
    if not user_data:
        conn.close()
        return None
    points, first_name, last_take_time = user_data
    c.execute('''SELECT b.building_id, b.name, b.complex, cb.conquered_date 
                 FROM conquered_buildings cb
                 JOIN buildings_info b ON cb.building_id = b.building_id
                 WHERE cb.user_id = ?
                 ORDER BY cb.conquered_date DESC''', (user_id,))
    conquered = c.fetchall()
    conquered_count = len(conquered)
    conn.close()
    return {
        'points': points,
        'first_name': first_name,
        'conquered': conquered,
        'conquered_count': conquered_count,
        'last_take_time': last_take_time
    }

def can_take_building(user_id, building_id):
    conn = sqlite3.connect('roofer_game.db')
    c = conn.cursor()
    c.execute("SELECT * FROM conquered_buildings WHERE user_id = ? AND building_id = ?", (user_id, building_id))
    if c.fetchone() is not None:
        conn.close()
        return False, "Ты уже брал этот ЖК!"
    c.execute("SELECT last_take_time FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result and result[0]:
        last_take = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
        profile = get_user_profile(user_id)
        cooldown_hours = get_cooldown_hours(profile['conquered_count'])
        time_since_last = datetime.now() - last_take
        if time_since_last < timedelta(hours=cooldown_hours):
            remaining = timedelta(hours=cooldown_hours) - time_since_last
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            return False, f"Нужно подождать ещё {hours} ч {minutes} мин до следующего взятия!"
    return True, "Можно брать"

def take_building(user_id, building_id):
    building = buildings[building_id]
    conn = sqlite3.connect('roofer_game.db')
    c = conn.cursor()
    c.execute("SELECT * FROM conquered_buildings WHERE user_id = ? AND building_id = ?", (user_id, building_id))
    if c.fetchone() is not None:
        conn.close()
        return False, "Ты уже брал этот ЖК!", False
    c.execute("SELECT last_take_time FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if result and result[0]:
        last_take = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
        profile = get_user_profile(user_id)
        cooldown_hours = get_cooldown_hours(profile['conquered_count'])
        time_since_last = datetime.now() - last_take
        if time_since_last < timedelta(hours=cooldown_hours):
            remaining = timedelta(hours=cooldown_hours) - time_since_last
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            conn.close()
            return False, f"Нужно подождать ещё {hours} ч {minutes} мин до следующего взятия!", False
    prim_active = check_prim(building)
    if prim_active:
        conn.close()
        return False, f"⚠️ Ты не смог заруфать жк {building['name']} и тебя приняли!", True
    points = building['points']
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO conquered_buildings (user_id, building_id, conquered_date, points_earned) VALUES (?, ?, ?, ?)",
              (user_id, building_id, current_time, points))
    c.execute("UPDATE users SET points = points + ?, last_take_time = ? WHERE user_id = ?", 
              (points, current_time, user_id))
    conn.commit()
    conn.close()
    profile = get_user_profile(user_id)
    next_cooldown = get_cooldown_hours(profile['conquered_count'])
    return True, f"✅ Ты взял {building['name']} и получил {points} очков!\n\nСледующее взятие будет доступно через {next_cooldown} ч.", False

def create_buildings_table():
    conn = sqlite3.connect('roofer_game.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS buildings_info
                 (building_id TEXT PRIMARY KEY,
                  name TEXT,
                  complex TEXT,
                  points INTEGER)''')
    for bid, info in buildings.items():
        c.execute("INSERT OR IGNORE INTO buildings_info (building_id, name, complex, points) VALUES (?, ?, ?, ?)",
                  (bid, info['name'], info['complex'], info['points']))
    conn.commit()
    conn.close()

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username, user.first_name)
    keyboard = [
        [InlineKeyboardButton("🏢 Руфить!", callback_data='roof_action')],
        [InlineKeyboardButton("📊 Портфолио руфера", callback_data='profile')],
        [InlineKeyboardButton("⏰ Проверить таймер", callback_data='check_timer')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Привет, {user.first_name}! Добро пожаловать в игру Руфер!\n\n"
        "Здесь ты можешь собирать очки, 'беря' разные жилые комплексы.\n"
        "Башни Москва-Сити оцениваются в 20 очков, Лахта Центр - 15 очков, остальные ЖК - по 10 очков.\n\n"
        "⚠️ Важно: при попытке взять ЖК есть шанс, что тебя 'примут':\n"
        "• Обычные ЖК - 30% шанс\n"
        "• Башни Москва-Сити - 70% шанс\n"
        "Если прим сработал, ЖК не засчитывается, и ты сможешь попробовать снова позже.\n\n"
        "⏰ Правила ожидания:\n"
        "• До 5 взятых ЖК - ожидание 1.5 часа\n"
        "• 5-9 взятых ЖК - ожидание 3 часа\n"
        "• 10-14 взятых ЖК - ожидание 4 часа\n"
        "• 15-19 взятых ЖК - ожидание 5 часов\n"
        "• От 20 взятых ЖК - ожидание 6 часов\n\n"
        "Нажимай кнопку 'Руфить!' чтобы начать!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_building(query, context, user_id, edit=True):
    available_buildings = context.user_data['available_buildings']
    current_index = context.user_data['current_index']
    building_id = available_buildings[current_index]
    building = buildings[building_id]
    context.user_data['current_building'] = building_id
    keyboard = [
        [InlineKeyboardButton("✅ Взять ЖК", callback_data='take_building')],
        [InlineKeyboardButton("⏭ Пропустить", callback_data='next_building')],
        [InlineKeyboardButton("📊 В портфолио", callback_data='profile')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    prim_chance = "70%" if is_moscow_city(building['complex']) else "30%"
    message_text = (
        f"🏢 {building['name']}\n"
        f"📍 Комплекс: {building['complex']}\n"
        f"💰 Очки: {building['points']}\n"
        f"⚠️ Шанс быть принятым: {prim_chance}\n\n"
        f"Прогресс: {current_index + 1}/{len(available_buildings)}"
    )
    try:
        with open(building['photo_path'], 'rb') as photo:
            if edit:
                await query.edit_message_media(
                    media=InputMediaPhoto(photo, caption=message_text),
                    reply_markup=reply_markup
                )
            else:
                await query.message.reply_photo(
                    photo=photo,
                    caption=message_text,
                    reply_markup=reply_markup
                )
                await query.message.delete()
    except Exception:
        if edit:
            await query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await query.message.reply_text(message_text, reply_markup=reply_markup)
            await query.message.delete()

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    register_user(user.id, user.username, user.first_name)
    
    if query.data == 'roof_action':
        available_buildings = []
        for bid, info in buildings.items():
            can_take, _ = can_take_building(user.id, bid)
            if can_take:
                available_buildings.append(bid)
        if not available_buildings:
            profile = get_user_profile(user.id)
            cooldown_hours = get_cooldown_hours(profile['conquered_count'])
            await query.edit_message_text(
                f"⏰ Ты уже взял все доступные на данный момент ЖК!\n\n"
                f"Ты взял {profile['conquered_count']} ЖК.\n"
                f"Следующее взятие будет доступно через {cooldown_hours} ч.\n\n"
                f"Всего в игре {len(buildings)} ЖК!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⏰ Проверить таймер", callback_data='check_timer'),
                    InlineKeyboardButton("📊 В портфолио", callback_data='profile')
                ]])
            )
            return
        random.shuffle(available_buildings)
        context.user_data['available_buildings'] = available_buildings
        context.user_data['current_index'] = 0
        await show_building(query, context, user.id)
    
    elif query.data == 'profile':
        profile = get_user_profile(user.id)
        if not profile:
            await query.edit_message_text("Профиль не найден. Начни игру с /start")
            return
        message = f"📊 Портфолио руфера {profile['first_name']}\n\n"
        message += f"💰 Всего очков: {profile['points']}\n"
        message += f"🏆 Взято ЖК: {profile['conquered_count']}/{len(buildings)}\n"
        if profile['last_take_time']:
            last_take = datetime.strptime(profile['last_take_time'], "%Y-%m-%d %H:%M:%S")
            cooldown_hours = get_cooldown_hours(profile['conquered_count'])
            time_since_last = datetime.now() - last_take
            if time_since_last < timedelta(hours=cooldown_hours):
                remaining = timedelta(hours=cooldown_hours) - time_since_last
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                message += f"⏰ Следующее взятие через: {hours} ч {minutes} мин\n\n"
            else:
                message += f"✅ Можно брать следующий ЖК!\n\n"
        message += "📋 Последние взятые ЖК:\n"
        if profile['conquered']:
            for building in profile['conquered'][:10]:
                message += f"• {building[1]} ({building[2]}) - {building[3]} очков\n"
            if len(profile['conquered']) > 10:
                message += f"... и ещё {len(profile['conquered']) - 10}\n"
        else:
            message += "Пока нет взятых ЖК. Нажми 'Руфить!' чтобы начать!\n"
        keyboard = [
            [InlineKeyboardButton("🏢 Продолжить руфить", callback_data='roof_action')],
            [InlineKeyboardButton("⏰ Проверить таймер", callback_data='check_timer')]
        ]
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == 'check_timer':
        profile = get_user_profile(user.id)
        if profile['last_take_time']:
            last_take = datetime.strptime(profile['last_take_time'], "%Y-%m-%d %H:%M:%S")
            cooldown_hours = get_cooldown_hours(profile['conquered_count'])
            time_since_last = datetime.now() - last_take
            if time_since_last < timedelta(hours=cooldown_hours):
                remaining = timedelta(hours=cooldown_hours) - time_since_last
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                message = f"⏰ Таймер ожидания:\n\n"
                message += f"Взято ЖК: {profile['conquered_count']}\n"
                message += f"Ожидание: {cooldown_hours} ч\n"
                message += f"Осталось ждать: {hours} ч {minutes} мин"
            else:
                message = f"✅ Можно брать следующий ЖК!\n\nВзято ЖК: {profile['conquered_count']}"
        else:
            message = "✅ Можно брать первый ЖК!"
        keyboard = [[InlineKeyboardButton("🏢 Руфить!", callback_data='roof_action')]]
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == 'take_building':
        if 'current_building' not in context.user_data:
            await query.edit_message_text("Произошла ошибка. Попробуй снова нажать 'Руфить!'")
            return
        building_id = context.user_data['current_building']
        success, msg, prim_triggered = take_building(user.id, building_id)
        if success:
            available = context.user_data.get('available_buildings', [])
            idx = context.user_data.get('current_index', 0)
            if idx + 1 < len(available):
                context.user_data['current_index'] = idx + 1
                await show_building(query, context, user.id, edit=False)
            else:
                prof = get_user_profile(user.id)
                await query.edit_message_text(
                    f"{msg}\n\n"
                    f"Ты просмотрел все доступные ЖК! Всего у тебя {prof['points']} очков.\n"
                    f"Взято ЖК: {prof['conquered_count']}/{len(buildings)}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("📊 В портфолио", callback_data='profile')
                    ]])
                )
        elif prim_triggered:
            await query.edit_message_text(
                f"{msg}\n\nПопробуй взять этот ЖК снова позже!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Попробовать снова", callback_data='roof_action'),
                    InlineKeyboardButton("📊 В портфолио", callback_data='profile')
                ]])
            )
        else:
            await query.edit_message_text(
                f"❌ {msg}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Показать другой", callback_data='roof_action')
                ]])
            )
    
    elif query.data == 'next_building':
        available = context.user_data.get('available_buildings', [])
        idx = context.user_data.get('current_index', 0)
        if idx + 1 < len(available):
            context.user_data['current_index'] = idx + 1
            await show_building(query, context, user.id, edit=False)
        else:
            await query.edit_message_text(
                "Больше нет доступных ЖК для показа!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📊 В портфолио", callback_data='profile')
                ]])
            )

# ========== ЗАПУСК ==========
def main():
    if not os.path.exists('photos'):
        os.makedirs('photos')
    init_db()
    create_buildings_table()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    loop = asyncio.get_event_loop()
    loop.create_task(start_webserver())
    print("Бот запущен...")
    print(f"Всего загружено ЖК: {len(buildings)}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
