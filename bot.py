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
)

API_URL = WEBAPP_URL.rstrip("/") + "/api/referral"


def send_message(chat_id, text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "reply_markup": {
                    "inline_keyboard": [
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
            },
            timeout=15
        )
    except Exception as e:
        print("Ошибка отправки:", e)


def process_start(user_id, start_parameter):
    """
    Если пользователь пришёл по:
    /start ref_123456

    отправляем данные в приложение.
    """

    if not start_parameter:
        return

    if not start_parameter.startswith("ref_"):
        return

    try:
        referrer_id = int(
            start_parameter.replace("ref_", "", 1)
        )
    except ValueError:
        return

    if referrer_id == user_id:
        return

    try:
        response = requests.post(
            API_URL,
            json={
                "secret": BOT_TOKEN,
                "user_id": user_id,
                "referrer_id": referrer_id
            },
            timeout=15
        )

        print(
            "Referral:",
            response.status_code,
            response.text
        )

    except Exception as e:
        print("Ошибка referral:", e)


def get_updates(offset=None):
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
            params={
                "timeout": 30,
                "offset": offset
            },
            timeout=35
        )

        return response.json()

    except Exception as e:
        print("Ошибка getUpdates:", e)
        return {
            "ok": False
        }


def main():

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не установлен")
        return

    print("🎁 GiftsUpp запущен")
    print("🤖 @" + BOT_USERNAME)
    print("⭐ Реферальная награда: 0.85 Stars")

    offset = None

    while True:

        result = get_updates(offset)

        if not result.get("ok"):
            time.sleep(3)
            continue

        updates = result.get(
            "result",
            []
        )

        for update in updates:

            offset = update["update_id"] + 1

            message = update.get(
                "message"
            )

            if not message:
                continue

            text = message.get(
                "text",
                ""
            )

            user = message.get(
                "from"
            )

            if not user:
                continue

            user_id = int(
                user["id"]
            )

            # Обрабатываем только /start
            if text.startswith("/start"):

                parts = text.split(
                    maxsplit=1
                )

                start_parameter = ""

                if len(parts) == 2:
                    start_parameter = parts[1].strip()

                # Сначала засчитываем реферала
                process_start(
                    user_id,
                    start_parameter
                )

                # Затем отправляем приветствие
                send_message(
                    user_id,
                    "🎁 Добро пожаловать в GiftsUpp!\n\n"
                    "⭐ Приглашай друзей и получай "
                    "0.85 Stars за каждого нового реферала.\n\n"
                    "👇 Открой приложение:"
                )

        time.sleep(0.2)


if __name__ == "__main__":
    main()
