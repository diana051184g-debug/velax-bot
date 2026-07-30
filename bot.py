import telebot
import os
import time
import re
import json
from datetime import datetime
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# === НАСТРОЙКИ VELAX31 ===
TOKEN = '8878411112:AAFaVrVm9no5idWcHmUqGqVnCU4EpXaCLGU'
telebot.apihelper.ENABLE_MIDDLEWARE = True
bot = telebot.TeleBot(TOKEN)
MY_ID = 5462607206  # Твой личный ID Максима
CHAT_ID = -1002914914953  # ID группы "Чатикс"
# =========================

TEXT_FILE = "rules_text.txt"
MEDIA_FILE = "rules_media.txt"
TYPE_FILE = "rules_type.txt"
CACHE_FILE = "users_cache.json"

LAST_MESSAGE_TIME = {}
FLOOD_DELAY = 1.0
USER_LAST_MESSAGES = {}
USER_SPAM_COUNT = {}

def load_user_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: return {}
    return {}

USER_ID_CACHE = load_user_cache()

def save_user_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(USER_ID_CACHE, f, ensure_ascii=False, indent=4)

BAD_WORDS = [
    "t.me/", "https://", "http://", "://vk.com", "приглашаю в канал", "подписывайтесь",
    "читы", "скачать читы", "взлом майнкрафт", "продам аккаунт", "купите голду", "читы на майнк",
    "шлюха", "пидор", "негр", "уебок", "хуесос", "админ пидорас", "сука", "блять", "нах"
]

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is alive 24/7!")
    def log_message(self, format, *args): return

Thread(target=lambda: HTTPServer(('', int(os.environ.get('PORT', 8080))), HealthCheckHandler).serve_forever(), daemon=True).start()

def load_rules_data():
    media_id, media_type = None, "text"
    text_data = "Привет! Правила канала Velax FAMILY еще не настроены. 🔥"
    if os.path.exists(MEDIA_FILE):
        with open(MEDIA_FILE, "r", encoding="utf-8") as f: media_id = f.read().strip() or None
    if os.path.exists(TYPE_FILE):
        with open(TYPE_FILE, "r", encoding="utf-8") as f: media_type = f.read().strip() or "text"
    if os.path.exists(TEXT_FILE):
        with open(TEXT_FILE, "r", encoding="utf-8") as f: text_data = f.read()
    return media_id, media_type, text_data

def save_rules_data(media_id, media_type, text_data):
    with open(TEXT_FILE, "w", encoding="utf-8") as f: f.write(text_data if text_data else "")
    with open(MEDIA_FILE, "w", encoding="utf-8") as f: f.write(media_id if media_id else "")
    with open(TYPE_FILE, "w", encoding="utf-8") as f: f.write(media_type if media_type else "text")

def parse_duration(duration_str):
    if not duration_str: return 86400
    if duration_str == '0': return 0
    match = re.match(r"(\d+)([smhd])", duration_str.lower())
    if not match: return 86400
    amount, unit = int(match.group(1)), match.group(2)
    if unit == 's': return amount
    if unit == 'm': return amount * 60
    if unit == 'h': return amount * 3600
    if unit == 'd': return amount * 86400
    return 86400
# 1. АВТО-ОТВЕТ НА ПОСТЫ ИЗ КАНАЛА
@bot.message_handler(func=lambda msg: msg.chat.id == CHAT_ID and (msg.forward_from_chat is not None or msg.from_user.username == "Channel_Bot" or getattr(msg, 'is_automatic_forward', False)))
def auto_reply_rules(message):
    media_id, media_type, rules_text = load_rules_data()
    try:
        if media_type == "animation" and media_id:
            bot.send_animation(CHAT_ID, media_id, caption=rules_text, reply_to_message_id=message.message_id, parse_mode='Markdown')
        elif media_type == "photo" and media_id:
            bot.send_photo(CHAT_ID, media_id, caption=rules_text, reply_to_message_id=message.message_id, parse_mode='Markdown')
        else:
            bot.reply_to(message, rules_text, parse_mode='Markdown')
    except Exception:
        if media_type == "animation" and media_id: bot.send_animation(CHAT_ID, media_id, caption=rules_text, reply_to_message_id=message.message_id)
        else: bot.reply_to(message, rules_text)

# 2. УПРАВЛЕНИЕ ИЗ ЛИЧКИ БОТА ДЛЯ МАКСИМА (/ban, /mute, /unban, /unmute)
@bot.message_handler(commands=['ban', 'mute', 'unmute', 'unban'], chat_types=['private'])
def private_admin_commands(message):
    if message.from_user.id != MY_ID: return

    args = message.text.split()
    command = args[0].lower()
    
    mentions = [word for word in args if word.startswith('@')]
    if not mentions:
        bot.reply_to(message, "❌ Ошибка! Укажите юзернейм нарушителя через @username.\nПример: `/mute @username 15m` или `/ban @username` 🛑")
        return
        
    username = mentions[0].replace('@', '').strip().lower()
    
    if username not in USER_ID_CACHE:
        bot.reply_to(message, f"❌ Пользователь @{username} не найден в базе бота! Он должен сначала написать хотя бы одно сообщение в группу.")
        return
        
    target_id = USER_ID_CACHE[username]
    now = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

    if command == '/mute':
        duration_str = args[2] if len(args) > 2 else "1d"
        seconds = parse_duration(duration_str)
        until_timestamp = int(time.time() + seconds)
        try:
            bot.restrict_chat_member(CHAT_ID, target_id, until_date=until_timestamp, can_send_messages=False)
            bot.reply_to(message, f"🤐 **Мут успешно выдан в чате!**\n👤 Нарушитель: @{username}\n🕒 Срок: `{duration_str}`")
        except Exception: bot.reply_to(message, "❌ Ошибка! Проверь права бота в чате.")

    elif command == '/ban':
        duration_str = args[2] if len(args) > 2 else "0"
        seconds = parse_duration(duration_str)
        until_timestamp = int(time.time() + seconds) if seconds > 0 else 0
        try:
            bot.ban_chat_member(CHAT_ID, target_id, until_date=until_timestamp)
            disp_time = f"на срок {duration_str}" if seconds > 0 else "НАВСЕГДА 🛑"
            bot.reply_to(message, f"🔨 **Бан успешно выдан в чате!**\n👤 Нарушитель: @{username}\n🕒 Срок: {disp_time}")
        except Exception: bot.reply_to(message, "❌ Ошибка бана.")

    elif command == '/unmute':
        try:
            bot.restrict_chat_member(CHAT_ID, target_id, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
            bot.reply_to(message, f"😇 **Размут выполнен!** Пользователь @{username} снова может писать в чате.")
        except Exception: bot.reply_to(message, "❌ Не удалось снять мут.")

    elif command == '/unban':
        try:
            bot.unban_chat_member(CHAT_ID, target_id, only_if_banned=True)
            bot.reply_to(message, f"🔓 **Разбан выполнен!** Пользователь @{username} удален из ЧС группы.")
        except Exception: bot.reply_to(message, "❌ Не удалось разбанить.")

# 3. ПОЛЬЗОВАТЕЛЬСКИЙ РЕПОРТ В ОБЩЕЙ ГРУППЕ «ЧАТИКС»
@bot.message_handler(func=lambda msg: msg.chat.id == CHAT_ID and (msg.text.lower().startswith(('/report', '!репорт', '!report'))))
def handle_report(message):
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Пишите команду в ответ на сообщение нарушителя!")
        return
    reported_user = message.reply_to_message.from_user
    bad_message = message.reply_to_message.text if message.reply_to_message.text else "[Медиа/Стикер]"
    now = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    report_notification = f"🚨 **РЕПОРТ В ЧАТИКС!**\n👤 От: @{message.from_user.username}\n🎯 На: @{reported_user.username}\n💬 Текст: _{bad_message}_\n🔗 Ссылка: https://t.me{str(CHAT_ID)[4:]}/{message.reply_to_message.message_id}"
    try:
        bot.send_message(MY_ID, report_notification, parse_mode='Markdown')
        bot.reply_to(message, "✅ Жалоба отправлена владельцу канала.")
    except Exception: pass

# 4. АВТО-МОДЕРАЦИЯ И КЭШИРОВАНИЕ В ГРУППЕ
@bot.message_handler(func=lambda msg: msg.chat.id == CHAT_ID)
def moderate_chatix(message):
    user_id = message.from_user.id
    if message.from_user.username:
        username_lower = message.from_user.username.lower()
        if USER_ID_CACHE.get(username_lower) != user_id:
            USER_ID_CACHE[username_lower] = user_id
            save_user_cache()

    if not message.text: return
    if message.forward_from_chat is not None or message.from_user.username == "Channel_Bot": return

    text_lower = message.text.lower()
    now = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

    if user_id in USER_LAST_MESSAGES:
        if USER_LAST_MESSAGES[user_id] == text_lower:
            USER_SPAM_COUNT[user_id] = USER_SPAM_COUNT.get(user_id, 1) + 1
            if USER_SPAM_COUNT[user_id] > 2:
                try:
                    bot.delete_message(CHAT_ID, message.message_id)
                    log_spam = f"🛡️ **СПАМ УДАЛЕН!**\n👤 Нарушитель: @{message.from_user.username}\n📈 Повторов: {USER_SPAM_COUNT[user_id]}\n💬 Текст: _{message.text}_"
                    bot.send_message(MY_ID, log_spam, parse_mode='Markdown')
                    return
                except Exception: pass
        else: USER_SPAM_COUNT[user_id] = 1
    USER_LAST_MESSAGES[user_id] = text_lower

    for word in BAD_WORDS:
        if word in text_lower:
            try:
                bot.delete_message(CHAT_ID, message.message_id)
                log_text = f"🛡️ **МАТ/ССЫЛКА УДАЛЕНА!**\n👤 От: @{message.from_user.username}\n🚫 Слово: `{word}`\n💬 Текст: _{message.text}_"
                bot.send_message(MY_ID, log_text, parse_mode='Markdown')
            except Exception: pass
            break

# 5. НАСТРОЙКА ИЗ ЛИЧКИ
user_state = {}
@bot.message_handler(commands=['start', 'setrules'], chat_types=['private'])
def private_commands(message):
    if message.from_user.id != MY_ID: return
    if message.text == '/start': bot.send_message(message.chat.id, "👋 Привет, Босс! Команды:\n/setrules — настроить правила.")
    elif message.text == '/setrules':
        user_state[message.from_user.id] = 'waiting_media_rules'
        bot.send_message(message.chat.id, "📝 Отправь мне ГИФКУ, а в подпись добавь текст правил!!")

@bot.message_handler(content_types=['animation', 'photo', 'text'], func=lambda msg: user_state.get(msg.from_user.id) == 'waiting_media_rules', chat_types=['private'])
def save_new_media_rules(message):
    if message.from_user.id != MY_ID: return
    media_id, media_type = None, "text"
    if message.content_type == 'animation': media_id, media_type = message.animation.file_id, "animation"
    elif message.content_type == 'photo': media_id, media_type = message.photo[-1].file_id, "photo"
    text_data = message.caption if message.caption else (message.text if message.content_type == 'text' else "")
    save_rules_data(media_id, media_type, text_data)
    user_state[message.from_user.id] = None
    bot.send_message(message.chat.id, "✅ Настройки обновлены.")

bot.infinity_polling()
