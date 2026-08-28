import os
import time
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    "GiftsUpp_bot"
)

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    "https://zxcpluaf2.onrender.com"
).rstrip("/")

# Награда за одного реферала
REFERRAL_REWARD = 0.85

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не установлен")


def telegram(method, data=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    try:
        response = requests.post(
            url,
            json=data or {},
            timeout=30
        )

        return response.json()

    except Exception as e:
        print("Telegram error:", e)
        return {}


def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    return telegram("sendMessage", data)


# Кнопка открытия приложения
def open_app_keyboard():
    return {
        "inline_keyboard": [
            [
                {
                    "text": "🎁 Открыть GiftsUpp",
                    "web_app": {
                        "url": WEBAPP_URL
                    }
                }
            ]
        ]
    }


# Реферальная ссылка Telegram
def get_ref_link(user_id):
    return (
        f"https://t.me/"
        f"{BOT_USERNAME}"
        f"?start=ref_{user_id}"
    )


# Отправляем реферала на сервер
def save_referral(user_id, referrer_id):

    if not referrer_id:
        return False

    try:
        user_id = int(user_id)
        referrer_id = int(referrer_id)

    except (TypeError, ValueError):
        return False

    # Нельзя пригласить самого себя
    if user_id == referrer_id:
        return False

    try:
        response = requests.post(
            f"{WEBAPP_URL}/api/referral",
            json={
                "user_id": user_id,
                "referrer_id": referrer_id,

                # Награда за реферала
                "reward": REFERRAL_REWARD,

                "secret": BOT_TOKEN
            },
            timeout=15
        )

        result = response.json()

        print(
            "REFERRAL:",
            user_id,
            "<-",
            referrer_id,
            "REWARD:",
            REFERRAL_REWARD,
            result
        )

        return result.get(
            "success",
            False
        )

    except Exception as e:

        print(
            "Referral API error:",
            e
        )

        return False


# /start
def handle_start(message):

    chat = message.get(
        "chat",
        {}
    )

    user = message.get(
        "from",
        {}
    )

    chat_id = chat.get("id")
    user_id = user.get("id")

    if not chat_id or not user_id:
        return

    text = message.get(
        "text",
        ""
    )

    parts = text.split(
        maxsplit=1
    )

    referrer_id = None

    # Получаем ref_XXXXXXXX
    if len(parts) > 1:

        argument = parts[1].strip()

        if argument.startswith("ref_"):

            try:
                referrer_id = int(
                    argument[4:]
                )

            except ValueError:
                referrer_id = None

    # Засчитываем реферала
    if referrer_id:

        counted = save_referral(
            user_id,
            referrer_id
        )

        print(
            "Referral counted:",
            counted
        )

    first_name = user.get(
        "first_name",
        "Пользователь"
    )

    send_message(
        chat_id,

        f"🎁 Привет, {first_name}!\n\n"
        "Добро пожаловать в GiftsUpp.\n\n"
        "⭐ Получай Stars\n"
        "👥 Приглашай друзей\n"
        "🏆 Участвуй в рейтинге\n\n"
        "Нажми кнопку ниже, чтобы открыть приложение.",

        open_app_keyboard()
    )


# /ref
def handle_referral_command(message):

    chat = message.get(
        "chat",
        {}
    )

    user = message.get(
        "from",
        {}
    )

    chat_id = chat.get("id")
    user_id = user.get("id")

    if not chat_id or not user_id:
        return

    ref_link = get_ref_link(
        user_id
    )

    keyboard = {
        "inline_keyboard": [

            [
                {
                    "text": "📤 Отправить реферала",
                    "switch_inline_query": (
                        "🎁 Заходи в GiftsUpp!\n\n"
                        + ref_link
                    )
                }
            ],

            [
                {
                    "text": "🎁 Открыть приложение",
                    "web_app": {
                        "url": WEBAPP_URL
                    }
                }
            ]

        ]
    }

    send_message(
        chat_id,

        "👥 Реферальная система GiftsUpp\n\n"
        "Приглашай друзей по своей ссылке.\n"
        f"⭐ За каждого нового реферала начисляется "
        f"{REFERRAL_REWARD:.2f} Stars на баланс.\n\n"
        f"🔗 {ref_link}",

        keyboard
    )


# Обработка Telegram updates
def process_update(update):

    message = update.get(
        "message"
    )

    if not message:
        return

    text = message.get(
        "text",
        ""
    )

    if text.startswith("/start"):

        handle_start(
            message
        )

    elif text.startswith("/ref"):

        handle_referral_command(
            message
        )


# Запуск бота
def main():

    print(
        "GiftsUpp bot started"
    )

    offset = 0

    while True:

        result = telegram(
            "getUpdates",
            {
                "offset": offset,
                "timeout": 25,
                "allowed_updates": [
                    "message"
                ]
            }
        )

        if not result.get("ok"):

            time.sleep(3)

            continue

        updates = result.get(
            "result",
            []
        )

        for update in updates:

            offset = (
                update["update_id"] + 1
            )

            try:

                process_update(
                    update
                )

            except Exception as e:

                print(
                    "Update error:",
                    e
                )

        time.sleep(0.2)


if __name__ == "__main__":
    main()
