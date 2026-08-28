import os
import time
import sqlite3
import threading
import requests

from flask import Flask, request, jsonify


# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    "GiftsUpp_bot"
)

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    "https://zxcpluaf2.onrender.com"
)

DB_FILE = "giftsupp.db"

REFERRAL_REWARD = 0.85


# =========================
# FLASK
# =========================

app = Flask(__name__)


# =========================
# DATABASE
# =========================

def get_db():
    conn = sqlite3.connect(
        DB_FILE,
        timeout=30
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            stars REAL NOT NULL DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            user_id INTEGER PRIMARY KEY,
            referrer_id INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def add_user(user_id):

    conn = get_db()

    conn.execute("""
        INSERT OR IGNORE INTO users
        (user_id, stars)
        VALUES (?, 0)
    """, (user_id,))

    conn.commit()
    conn.close()


# =========================
# REFERRAL API
# =========================

@app.route(
    "/api/referral",
    methods=["POST"]
)
def api_referral():

    data = request.get_json(
        silent=True
    ) or {}

    secret = data.get("secret")

    user_id = data.get("user_id")
    referrer_id = data.get("referrer_id")

    # Проверяем секрет
    if not BOT_TOKEN:
        return jsonify(
            success=False,
            error="BOT_TOKEN не установлен"
        ), 500

    if secret != BOT_TOKEN:
        return jsonify(
            success=False,
            error="Неверный secret"
        ), 403

    # Проверяем ID
    try:
        user_id = int(user_id)
        referrer_id = int(referrer_id)
    except (TypeError, ValueError):
        return jsonify(
            success=False,
            error="Неверный user_id или referrer_id"
        ), 400

    # Нельзя пригласить самого себя
    if user_id == referrer_id:
        return jsonify(
            success=False,
            error="Нельзя пригласить самого себя"
        ), 400

    conn = get_db()

    try:

        # Создаём пользователей
        conn.execute("""
            INSERT OR IGNORE INTO users
            (user_id, stars)
            VALUES (?, 0)
        """, (user_id,))

        conn.execute("""
            INSERT OR IGNORE INTO users
            (user_id, stars)
            VALUES (?, 0)
        """, (referrer_id,))

        # Проверяем, был ли уже реферал
        existing = conn.execute("""
            SELECT user_id
            FROM referrals
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        if existing:
            conn.commit()
            conn.close()

            return jsonify(
                success=True,
                already_counted=True,
                reward=0
            )

        # Записываем реферала
        conn.execute("""
            INSERT INTO referrals
            (user_id, referrer_id)
            VALUES (?, ?)
        """, (
            user_id,
            referrer_id
        ))

        # Начисляем 0.85 Stars пригласившему
        conn.execute("""
            UPDATE users
            SET stars = stars + ?
            WHERE user_id = ?
        """, (
            REFERRAL_REWARD,
            referrer_id
        ))

        conn.commit()

        conn.close()

        print(
            f"⭐ Referral: {referrer_id} "
            f"получил {REFERRAL_REWARD} Stars "
            f"за пользователя {user_id}"
        )

        return jsonify(
            success=True,
            already_counted=False,
            reward=REFERRAL_REWARD
        )

    except Exception as e:

        conn.rollback()
        conn.close()

        print(
            "Ошибка referral:",
            e
        )

        return jsonify(
            success=False,
            error="Ошибка базы данных"
        ), 500


# =========================
# TELEGRAM
# =========================

def send_message(chat_id, text):

    if not BOT_TOKEN:
        return

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

        print(
            "Ошибка отправки:",
            e
        )


def process_start(
    user_id,
    start_parameter
):

    if not start_parameter:
        return

    if not start_parameter.startswith(
        "ref_"
    ):
        return

    try:

        referrer_id = int(
            start_parameter.replace(
                "ref_",
                "",
                1
            )
        )

    except ValueError:

        return

    if referrer_id == user_id:
        return

    try:

        response = requests.post(
            f"{WEBAPP_URL.rstrip('/')}/api/referral",
            json={
                "secret": BOT_TOKEN,
                "user_id": user_id,
                "referrer_id": referrer_id
            },
            timeout=15
        )

        print(
            "Referral API:",
            response.status_code,
            response.text
        )

    except Exception as e:

        print(
            "Ошибка referral:",
            e
        )


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

        print(
            "Ошибка getUpdates:",
            e
        )

        return {
            "ok": False
        }


def telegram_bot():

    if not BOT_TOKEN:

        print(
            "❌ BOT_TOKEN не установлен"
        )

        return

    print(
        "🎁 GiftsUpp запущен"
    )

    print(
        "🤖 @" + BOT_USERNAME
    )

    print(
        "⭐ Реферальная награда: 0.85 Stars"
    )

    offset = None

    while True:

        result = get_updates(
            offset
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

            add_user(
                user_id
            )

            if text.startswith(
                "/start"
            ):

                parts = text.split(
                    maxsplit=1
                )

                start_parameter = ""

                if len(parts) == 2:

                    start_parameter = (
                        parts[1].strip()
                    )

                # Сначала реферал
                process_start(
                    user_id,
                    start_parameter
                )

                # Затем сообщение
                send_message(
                    user_id,
                    "🎁 Добро пожаловать "
                    "в GiftsUpp!\n\n"
                    "⭐ Приглашай друзей и "
                    "получай 0.85 Stars "
                    "за каждого нового "
                    "реферала.\n\n"
                    "👇 Открой приложение:"
                )

        time.sleep(0.2)


# =========================
# ЗАПУСК
# =========================

init_db()


if __name__ == "__main__":

    # Telegram запускаем отдельно
    thread = threading.Thread(
        target=telegram_bot,
        daemon=True
    )

    thread.start()

    # Render должен видеть этот порт
    port = int(
    os.environ.get(
        "PORT",
        10000
    )
)

app.run(
    host="0.0.0.0",
    port=port
)
