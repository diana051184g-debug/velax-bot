import telebot
import os
import time
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# === НАСТРОЙКИ VELAX31 ===
TOKEN = '8878411112:AAFaVrVm9no5idWcHmUqGqVnCU4EpXaCLGU'
telebot.apihelper.ENABLE_MIDDLEWARE = True
bot = telebot.TeleBot(TOKEN)
MY_ID = 5462607206
CHAT_ID = -1002914914953
# =========================

# Файлы базы данных
TEXT_FILE = "rules_text.txt"
VIDEO_FILE = "rules_video.txt"
LAST_MESSAGE_TIME = {}
FLOOD_DELAY = 1.5

# Встроенный веб-сервер для обмана хостинга (Ping-Pong)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is alive 24/7!")
    def log_message(self, format, *args):
        return

def run_health_server():
    server_address = ('', int(os.environ.get('PORT', 8080)))
    httpd = HTTPServer(server_address, HealthCheckHandler)
    httpd.serve_forever()

# Запускаем обманщик в отдельном потоке
Thread(target=run_health_server, daemon=True).start()

def load_rules_data():
    video_id = None
    text_data = "Привет! Правила канала Velax FAMILY еще не настроены. Веди себя хорошо! 🔥"
    if os.path.exists(VIDEO_FILE):
        with open(VIDEO_FILE, "r", encoding="utf-8") as f:
            video_id = f.read().strip() or None
    if os.path.exists(TEXT_FILE):
        with open(TEXT_FILE, "r", encoding="utf-8") as f:
            text_data = f.read()
    return video_id, text_data

def save_rules_data(video_id, text_data):
    with open(TEXT_FILE, "w", encoding="utf-8") as f:
        f.write(text_data if text_data else "")
    with open(VIDEO_FILE, "w", encoding="utf-8") as f:
        f.write(video_id if video_id else "")

@bot.middleware_handler(update_types=['message'])
def anti_flood_middleware(bot_instance, message):
    user_id = message.from_user.id
    current_time = time.time()
    if user_id in LAST_MESSAGE_TIME:
        if current_time - LAST_MESSAGE_TIME[user_id] < FLOOD_DELAY:
            return False
    LAST_MESSAGE_TIME[user_id] = current_time

@bot.message_handler(func=lambda msg: msg.chat.id == CHAT_ID and msg.from_user.username == "Channel_Bot")
def auto_reply_rules(message):
    video_id, rules_text = load_rules_data()
    try:
        if video_id:
            bot.send_video(CHAT_ID, video_id, caption=rules_text, reply_to_message_id=message.message_id, parse_mode='Markdown')
        else:
            bot.reply_to(message, rules_text, parse_mode='Markdown')
    except Exception:
        if video_id:
            bot.send_video(CHAT_ID, video_id, caption=rules_text, reply_to_message_id=message.message_id)
        else:
            bot.reply_to(message, rules_text)

user_state = {}

@bot.message_handler(commands=['start', 'setrules'], chat_types=['private'])
def private_commands(message):
    if message.from_user.id != MY_ID:
        bot.send_message(message.chat.id, "❌ Доступ закрыт.")
        return
    if message.text == '/start':
        bot.send_message(message.chat.id, "👋 Привет, Босс! Команды:\n/setrules — настроить видео и текст правил.")
    elif message.text == '/setrules':
        user_state[message.from_user.id] = 'waiting_media_rules'
        bot.send_message(message.chat.id, "📝 Отправь мне ВИДЕО, а в описание добавь текст правил!")

@bot.message_handler(content_types=['video', 'video_note', 'text'], func=lambda msg: user_state.get(msg.from_user.id) == 'waiting_media_rules', chat_types=['private'])
def save_new_media_rules(message):
    if message.from_user.id != MY_ID:
        return
    video_id, text_data = None, ""
    if message.content_type == 'video':
        video_id = message.video.file_id
        text_data = message.caption if message.caption else ""
    elif message.content_type == 'video_note':
        video_id = message.video_note.file_id
        text_data = "Смотри правила на видео выше! 🔥"
    elif message.content_type == 'text':
        text_data = message.text
    save_rules_data(video_id, text_data)
    user_state[message.from_user.id] = None
    bot.send_message(message.chat.id, "✅ Настройки сохранены в базу облака.")

@bot.message_handler(func=lambda msg: msg.chat.id == CHAT_ID and (msg.text.lower().startswith('!репорт') or msg.text.lower().startswith('!report')))
def handle_report(message):
    if not message.reply_to_message:
        bot.reply_to(message, "❌ Пиши в ответ на сообщение нарушителя!")
        return
    reported_user = message.reply_to_message.from_user
    bad_message = message.reply_to_message.text if message.reply_to_message.text else "[Медиа/Стикер]"
    report_notification = f"🚨 **ЖАЛОБА ЧАТИКС!**\n\n👤 От: @{message.from_user.username}\n🎯 На: @{reported_user.username}\n💬 Текст: _{bad_message}_"
    try:
        bot.send_message(MY_ID, report_notification, parse_mode='Markdown')
        bot.reply_to(message, "✅ Жалоба отправлена.")
    except Exception:
        bot.reply_to(message, "❌ Ошибка отправки репорта.")

print("Код для вечного облака готов!")
bot.infinity_polling()
