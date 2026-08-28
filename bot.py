# 1. Перейди по этой ссылке в браузере, чтобы получить токен Яндекса:
# https://oauth.yandex.ru/authorize?response_type=token&client_id=4e8511f921b549bea53c420a09b2b776

import telebot
import os
import base64
import json
import requests
import yadisk

TOKEN = '8924714730:AAHKD7qWectpQGm3WcLJdOhcoXRKQQDQ_A0'
bot = telebot.TeleBot(TOKEN)

# ⚠️ Вставь сюда полученный токен Яндекса в кавычки вместо 'ТВОЙ_ТОКЕН_С_ЯХДЕНКСА'
YANDEX_TOKEN = 'ТВОЙ_ТОКЕН_С_ЯХДЕНКСА'
y = yadisk.YaDisk(token=YANDEX_TOKEN)

if not os.path.exists("Data"):
    os.makedirs("Data")

def load_stats():
    if os.path.exists("Data.json"):
        with open("Data.json", 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def encode_filename(filename):
    return base64.urlsafe_b64encode(filename.encode()).decode().rstrip('=')

def decode_filename(encoded):
    padding = 4 - (len(encoded) % 4)
    if padding != 4:
        encoded += '=' * padding
    return base64.urlsafe_b64decode(encoded).decode()

@bot.message_handler(commands=['help'])
def info(message):
    bot.send_message(message.chat.id, "по всем вопросам писать @sixsliven66")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if len(message.text.split()) > 1:
        try:
            comand, file = message.text.replace("/start", "").strip().split("-", 1)
            file = decode_filename(file)
        except Exception:
            bot.send_message(message.chat.id, "❌ Неверный формат ссылки")
            return

        file_path = f"Data/{file}"
        if os.path.exists(file_path):
            data = load_stats()
            data[file] = data.get(file, 0) + 1

            with open('Data.json', 'w', encoding='utf-8') as d:
                json.dump(data, d, ensure_ascii=False, indent=4)

            with open(file_path, 'rb') as f:
                if comand == "getPhoto":
                    bot.send_photo(message.chat.id, f, caption=f"📸 {data[file]} просмотра")
                elif comand == "getVid":
                    bot.send_message(
                        message.chat.id, 
                        f"👁 Просмотров: {data[file]}\n\n"
                        f"📁 Файл сохранен в облаке."
                    )
        else:
            bot.send_message(message.chat.id, "нету такой сылки")
    else:
        welcome_text = (
            "Привет! 👋\n\n"
            "Я помогу тебе поделиться любым медиафайлом (фото, видео, документы, аудио, голосовые) с подписчиками твоего канала.\n"
            "Отправь файл любого из перечисленных типов, а я в ответ дам тебе ссылку. Желательно указать подпись, чтобы человек не забыл, кто ему это пошарил.\n"
            "Также ты можешь подключить свой канал или чат и установить ограничение на доступ к медиафайлу только своим подписчикам.\n\n"
            "/settings - для более тонкой настройки\n\n"
            "Владелец бота не несёт ответственности за передаваемые файлы. Всё содержимое создаётся и загружается пользователями."
        )
        bot.send_message(message.chat.id, welcome_text)

@bot.message_handler(content_types=['photo', 'video', 'document', 'audio', 'voice'])
def handle_media(message):
    if message.photo:
        file = message.photo[-1]
        file_name = f"photo_{message.chat.id}_{file.file_unique_id}.jpg"
        media_type = "Photo"
    elif message.video:
        file = message.video
        file_name = f"video_{message.chat.id}_{file.file_unique_id}.mp4"
        media_type = "Vid"
    elif message.document:
        file = message.document
        file_name = f"doc_{message.chat.id}_{file.file_unique_id}_{file.file_name}"
        media_type = "Vid"
    elif message.audio:
        file = message.audio
        file_name = f"audio_{message.chat.id}_{file.file_unique_id}_{file.file_name}"
        media_type = "Vid"
    elif message.voice:
        file = message.voice
        file_name = f"voice_{message.chat.id}_{file.file_unique_id}.ogg"
        media_type = "Vid"
    else:
        bot.reply_to(message, "❌ Отправьте поддерживаемый медиафайл")
        return

    msg = bot.reply_to(message, "⏳ Загружаю файл на Яндекс.Диск...")

    try:
        file_info = bot.get_file(file.file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        
        local_path = os.path.join("Data", file_name)
        
        response = requests.get(file_url, stream=True)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
            
            if not y.exists("/BotUploads"):
                y.mkdir("/BotUploads")
                
            y_path = f"/BotUploads/{file_name}"
            y.upload(local_path, y_path, overwrite=True)
            
            try:
                y.publish(y_path)
            except Exception:
                pass
                
            public_file_info = y.get_meta(y_path)
            download_link = public_file_info.public_url

            if os.path.exists(local_path):
                os.remove(local_path)

            short_code = encode_filename(file_name)
            bot.edit_message_text(
                f"✅ Файл успешно загружен!\n\n"
                f"🔗 Прямая ссылка на скачивание:\n{download_link}\n\n"
                f"🤖 Ссылка для бота:\nhttps://t.me/SixslivenVideo_bot?start=get{media_type}-{short_code}",
                message.chat.id,
                msg.message_id
            )
        else:
            bot.edit_message_text("❌ Ошибка при скачивании файла.", message.chat.id, msg.message_id)
            
    except Exception as e:
        print(e)
        bot.edit_message_text(f"❌ Произошла ошибка: {e}", message.chat.id, msg.message_id)

bot.infinity_polling()
