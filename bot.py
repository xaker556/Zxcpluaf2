import os
import sqlite3
import json
import hmac
import hashlib
import urllib.parse
import requests
import threading
import time

from flask import Flask, request, jsonify, send_from_directory


app = Flask(__name__)


# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    "GiftsUpp_bot"
)

CHANNEL = "@eclipsedlf"

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    "https://zxcpluaf2.onrender.com"
)

REFERRAL_REWARD = 0.85

DB_FILE = "giftsupp.db"


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
            telegram_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            balance REAL DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            referred_by INTEGER,
            created_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)

    conn.commit()
    conn.close()


# =========================
# TELEGRAM AUTH
# =========================

def telegram_user(init_data):
    if not BOT_TOKEN or not init_data:
        return None

    try:
        data = dict(
            urllib.parse.parse_qsl(
                init_data
            )
        )

        received_hash = data.pop(
            "hash",
            None
        )

        if not received_hash:
            return None

        check_string = "\n".join(
            f"{key}={data[key]}"
            for key in sorted(data)
        )

        secret_key = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()

        calculated = hmac.new(
            secret_key,
            check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            calculated,
            received_hash
        ):
            return None

        user = json.loads(
            data.get(
                "user",
                "{}"
            )
        )

        if not user.get("id"):
            return None

        return user

    except Exception:
        return None


# =========================
# SUBSCRIPTION
# =========================

def is_subscribed(user_id):
    if not BOT_TOKEN:
        return False

    try:
        response = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember",
            params={
                "chat_id": CHANNEL,
                "user_id": user_id
            },
            timeout=10
        )

        result = response.json()

        if not result.get("ok"):
            return False

        status = result["result"]["status"]

        return status in (
            "member",
            "administrator",
            "creator"
        )

    except Exception:
        return False


# =========================
# USER
# =========================

def create_or_update_user(
    user_id,
    username="",
    first_name=""
):
    conn = get_db()

    row = conn.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id=?
        """,
        (user_id,)
    ).fetchone()

    if row is None:
        conn.execute(
            """
            INSERT INTO users (
                telegram_id,
                username,
                first_name
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                username,
                first_name
            )
        )
    else:
        conn.execute(
            """
            UPDATE users
            SET username=?,
                first_name=?
            WHERE telegram_id=?
            """,
            (
                username,
                first_name,
                user_id
            )
        )

    conn.commit()

    row = conn.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id=?
        """,
        (user_id,)
    ).fetchone()

    conn.close()

    return row


# =========================
# РЕФЕРАЛ
# =========================

def process_referral(
    user_id,
    referrer_id
):
    try:
        user_id = int(user_id)
        referrer_id = int(referrer_id)
    except (TypeError, ValueError):
        return False

    if user_id == referrer_id:
        return False

    conn = get_db()

    # Проверяем пригласившего
    referrer = conn.execute(
        """
        SELECT telegram_id
        FROM users
        WHERE telegram_id=?
        """,
        (referrer_id,)
    ).fetchone()

    if not referrer:
        conn.close()
        return False

    # Проверяем пользователя
    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id=?
        """,
        (user_id,)
    ).fetchone()

    # Пользователь уже существует
    if user:

        # Уже есть пригласивший
        if user["referred_by"] is not None:
            conn.close()
            return False

        conn.execute(
            """
            UPDATE users
            SET referred_by=?
            WHERE telegram_id=?
            """,
            (
                referrer_id,
                user_id
            )
        )

    else:

        # Новый пользователь
        conn.execute(
            """
            INSERT INTO users (
                telegram_id,
                referred_by
            )
            VALUES (?, ?)
            """,
            (
                user_id,
                referrer_id
            )
        )

    # +1 реферал
    # +0.85 Stars
    conn.execute(
        """
        UPDATE users
        SET referrals = referrals + 1,
            balance = balance + ?
        WHERE telegram_id=?
        """,
        (
            REFERRAL_REWARD,
            referrer_id
        )
    )

    conn.commit()
    conn.close()

    return True


# =========================
# TELEGRAM API
# =========================

def telegram_api(method, data=None):
    if not BOT_TOKEN:
        return None

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",
            json=data or {},
            timeout=20
        )

        return response.json()

    except Exception:
        return None


# =========================
# START BOT
# =========================

def handle_start(message):
    if not message:
        return

    chat = message.get(
        "chat",
        {}
    )

    user = message.get(
        "from",
        {}
    )

    user_id = user.get("id")

    if not user_id:
        return

    username = user.get(
        "username",
        ""
    )

    first_name = user.get(
        "first_name",
        ""
    )

    create_or_update_user(
        user_id,
        username,
        first_name
    )

    text = message.get(
        "text",
        ""
    )

    parts = text.split(
        maxsplit=1
    )

    start_parameter = ""

    if len(parts) > 1:
        start_parameter = parts[1].strip()

    # -------------------------
    # РЕФЕРАЛЬНАЯ ССЫЛКА
    # -------------------------

    if start_parameter.startswith("ref_"):

        referrer_id = start_parameter[4:]

        counted = process_referral(
            user_id,
            referrer_id
        )

        if counted:
            send_message(
                chat["id"],
                "🎉 Реферал засчитан!\n\n"
                "Пригласившему начислено "
                "⭐ 0.85 Stars."
            )


    # -------------------------
    # КНОПКА APP
    # -------------------------

    keyboard = {
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

    send_message(
        chat["id"],
        "🎁 Добро пожаловать в GiftsUpp!\n\n"
        "⭐ Приглашай друзей и получай "
        "0.85 Stars за каждого нового "
        "реферала.\n\n"
        "👇 Открой приложение:",
        keyboard
    )


def send_message(
    chat_id,
    text,
    reply_markup=None
):
    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup:
        data["reply_markup"] = reply_markup

    return telegram_api(
        "sendMessage",
        data
    )


# =========================
# BOT POLLING
# =========================

def bot_polling():

    if not BOT_TOKEN:
        print(
            "BOT_TOKEN не установлен"
        )
        return

    print(
        "Telegram bot polling started"
    )

    offset = 0

    while True:

        try:

            result = telegram_api(
                "getUpdates",
                {
                    "offset": offset,
                    "timeout": 25,
                    "allowed_updates": [
                        "message"
                    ]
                }
            )

            if not result or not result.get("ok"):
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

                if text.startswith(
                    "/start"
                ):
                    handle_start(
                        message
                    )

        except Exception as error:

            print(
                "Polling error:",
                error
            )

            time.sleep(5)


# =========================
# WEB APP
# =========================

@app.route("/")
def home():

    return send_from_directory(
        ".",
        "index.html"
    )


# =========================
# API ME
# =========================

@app.route(
    "/api/me",
    methods=["POST"]
)
def api_me():

    data = request.get_json(
        silent=True
    ) or {}

    user = telegram_user(
        data.get("initData")
    )

    if not user:

        return jsonify(
            success=False,
            error="Telegram не подтверждён"
        ), 401

    uid = int(
        user["id"]
    )

    if not is_subscribed(uid):

        return jsonify(
            success=False,
            error="Сначала подпишитесь"
        ), 403

    row = create_or_update_user(
        uid,
        user.get(
            "username",
            ""
        ),
        user.get(
            "first_name",
            ""
        )
    )

    ref_link = (
        f"https://t.me/"
        f"{BOT_USERNAME}"
        f"?start=ref_{uid}"
    )

    return jsonify(
        success=True,
        telegram_id=row["telegram_id"],
        username=row["username"],
        first_name=row["first_name"],
        balance=row["balance"],
        referrals=row["referrals"],
        ref_link=ref_link
    )


# =========================
# CHECK SUBSCRIPTION
# =========================

@app.route(
    "/api/check-subscription",
    methods=["POST"]
)
def api_check_subscription():

    data = request.get_json(
        silent=True
    ) or {}

    user = telegram_user(
        data.get("initData")
    )

    if not user:

        return jsonify(
            subscribed=False
        ), 401

    return jsonify(
        subscribed=is_subscribed(
            int(user["id"])
        )
    )


# =========================
# LEADERS
# =========================

@app.route(
    "/api/leaders"
)
def api_leaders():

    conn = get_db()

    rows = conn.execute(
        """
        SELECT
            username,
            first_name,
            referrals
        FROM users
        WHERE referrals > 0
        ORDER BY
            referrals DESC,
            created_at ASC
        LIMIT 20
        """
    ).fetchall()

    conn.close()

    leaders = []

    for row in rows:

        if row["username"]:
            name = (
                "@" +
                row["username"]
            )
        else:
            name = (
                row["first_name"]
                or "Пользователь"
            )

        leaders.append({
            "name": name,
            "referrals": row["referrals"]
        })

    return jsonify(
        success=True,
        leaders=leaders
    )


# =========================
# WITHDRAW
# =========================

@app.route(
    "/api/withdraw",
    methods=["POST"]
)
def api_withdraw():

    data = request.get_json(
        silent=True
    ) or {}

    user = telegram_user(
        data.get("initData")
    )

    if not user:

        return jsonify(
            success=False,
            error="Telegram не подтверждён"
        ), 401

    uid = int(
        user["id"]
    )

    if not is_subscribed(uid):

        return jsonify(
            success=False,
            error="Сначала подпишитесь"
        ), 403

    try:

        amount = float(
            data.get("amount")
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify(
            success=False,
            error="Некорректная сумма"
        ), 400

    if amount <= 0:

        return jsonify(
            success=False,
            error="Некорректная сумма"
        ), 400

    if not BOT_TOKEN or not ADMIN_CHAT_ID:

        return jsonify(
            success=False,
            error="Настройки Telegram не установлены"
        ), 500

    conn = get_db()

    row = conn.execute(
        """
        SELECT balance
        FROM users
        WHERE telegram_id=?
        """,
        (uid,)
    ).fetchone()

    if not row:

        conn.close()

        return jsonify(
            success=False,
            error="Пользователь не найден"
        ), 404

    balance = float(
        row["balance"]
    )

    if amount > balance:

        conn.close()

        return jsonify(
            success=False,
            error="Недостаточно Stars"
        ), 400

    username = user.get(
        "username",
        ""
    )

    first_name = user.get(
        "first_name",
        ""
    )

    display_name = (
        "@" + username
        if username
        else first_name
        or "Не указан"
    )

    text = (
        "💸 НОВАЯ ЗАЯВКА НА ВЫВОД\n\n"
        f"👤 Пользователь: {display_name}\n"
        f"🆔 Telegram ID: {uid}\n"
        f"⭐ Сумма: {amount:g} Stars\n"
        f"💰 Баланс: {balance:g} Stars"
    )

    result = telegram_api(
        "sendMessage",
        {
            "chat_id": ADMIN_CHAT_ID,
            "text": text
        }
    )

    if not result or not result.get("ok"):

        conn.close()

        return jsonify(
            success=False,
            error="Telegram не принял заявку"
        ), 500

    new_balance = (
        balance - amount
    )

    conn.execute(
        """
        UPDATE users
        SET balance=?
        WHERE telegram_id=?
        """,
        (
            new_balance,
            uid
        )
    )

    conn.commit()
    conn.close()

    return jsonify(
        success=True,
        balance=new_balance
    )


# =========================
# START
# =========================

init_db()


if __name__ == "__main__":

    if BOT_TOKEN:

        thread = threading.Thread(
            target=bot_polling,
            daemon=True
        )

        thread.start()

    port = int(
        os.getenv(
            "PORT",
            "10000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
