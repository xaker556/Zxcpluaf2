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

# Функция для загрузки данных с защитой от пустых или поврежденных файлов
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

# Функция для сохранения данных
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

if __name__ == '__main__':
    print("Бот запущен...")
    # Запуск бесконечного опроса сервера Telegram
    bot.infinity_polling(skip_pending=True)

