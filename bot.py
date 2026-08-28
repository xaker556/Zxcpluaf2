# -*- coding: utf-8 -*-
import os
import json
import telebot

# Получаем токены из переменных окружения Render
TOKEN = os.getenv('TOKEN')
YANDEX_TOKEN = os.getenv('YANDEX_TOKEN')

if not TOKEN:
    raise ValueError("Не задан токен телеграм-бота в переменной окружения TOKEN!")

bot = telebot.TeleBot(TOKEN)

DATA_FILE = 'Data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return {}
            return json.loads(content)
    except Exception as e:
        print(f"Ошибка чтения данных: {e}")
        return {}

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка сохранения данных: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        bot.reply_to(message, "Бот успешно запущен и работает в облаке!")
    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")

# Обработчик фотографий
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        # Получаем информацию о самом качественном фото
        photo = message.photo[-1]
        file_id = photo.file_id
        
        # Отвечаем пользователю, что фото получено
        bot.reply_to(message, f"Фото успешно получено! ID файла: {file_id}")
    except Exception as e:
        print(f"❌ Ошибка при обработке фото: {e}")
        bot.reply_to(message, "Произошла ошибка при обработке фотографии.")

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling(skip_pending=True)
