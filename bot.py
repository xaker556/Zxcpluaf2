import os
import sqlite3
import json
import hmac
import hashlib
import urllib.parse
import requests

from flask import Flask, request, jsonify, Response

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

CHANNEL = "@eclipsedlf"
CHANNEL_URL = "https://t.me/eclipsedlf"

DB_FILE = "giftsupp.db"


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            balance REAL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def telegram_user(init_data):
    if not BOT_TOKEN or not init_data:
        return None

    try:
        data = dict(urllib.parse.parse_qsl(init_data))
        received_hash = data.pop("hash", None)

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

        calculated_hash = hmac.new(
            secret_key,
            check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            calculated_hash,
            received_hash
        ):
            return None

        user = json.loads(data.get("user", "{}"))

        if not user.get("id"):
            return None

        return user

    except Exception:
        return None


def is_subscribed(user_id):
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

        return status in [
            "member",
            "administrator",
            "creator"
        ]

    except Exception:
        return False


HTML = """
<!DOCTYPE html>
<html lang="ru">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>GiftsUpp</title>

<script src="https://telegram.org/js/telegram-web-app.js"></script>

<style>

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    background: #100b16;
    color: white;
    font-family: Arial, sans-serif;
}

.app {
    max-width: 430px;
    margin: auto;
    min-height: 100vh;
    padding-bottom: 90px;
}

header {
    padding: 28px 20px 18px;
}

.logo {
    font-size: 26px;
    font-weight: 800;
}

.subtitle {
    color: #8d8295;
    margin-top: 5px;
    font-size: 13px;
}

.card {
    margin: 12px 16px;
    padding: 20px;
    background: #19121f;
    border: 1px solid #30223a;
    border-radius: 18px;
}

.balance {
    font-size: 32px;
    font-weight: 800;
    margin-top: 8px;
}

.user {
    font-weight: 700;
}

.id {
    color: #8d8295;
    font-size: 12px;
    margin-top: 5px;
}

.grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin: 16px;
}

button {
    width: 100%;
    padding: 16px 10px;
    border-radius: 14px;
    border: 1px solid #30223a;
    background: #21172b;
    color: white;
    font-size: 14px;
}

input {
    width: 100%;
    padding: 14px;
    margin-top: 10px;
    background: #100b16;
    border: 1px solid #3a2b44;
    border-radius: 12px;
    color: white;
}

.page {
    display: none;
}

.page.active {
    display: block;
}

.bottom {
    position: fixed;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 100%;
    max-width: 430px;
    padding: 10px;
    display: flex;
    gap: 10px;
    background: #130d19;
}

.notice {
    margin: 12px 16px;
    padding: 15px;
    background: #1c1424;
    border-radius: 14px;
    color: #aaa;
}

#subscribe {
    position: fixed;
    inset: 0;
    background: #100b16;
    z-index: 100;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.subscribe-box {
    background: #19121f;
    border: 1px solid #30223a;
    border-radius: 20px;
    padding: 25px;
    text-align: center;
}

.subscribe-box h2 {
    margin-bottom: 12px;
}

.subscribe-box p {
    color: #aaa;
    margin-bottom: 20px;
}

</style>

</head>

<body>


<div id="subscribe">

    <div class="subscribe-box">

        <h2>📢 Подписка</h2>

        <p>
        Чтобы пользоваться GiftsUpp,
        подпишитесь на @eclipsedlf
        </p>

        <button onclick="openChannel()">
            📢 Подписаться
        </button>

        <br><br>

        <button onclick="checkSubscription()">
            ✅ Я подписался
        </button>

        <div id="subMessage"></div>

    </div>

</div>


<div class="app">


<div id="home" class="page active">

<header>

<div class="logo">
🎁 GiftsUpp
</div>

<div class="subtitle">
Подарки • Stars • Рефералы
</div>

</header>


<div class="card">

<div class="subtitle">
Ваш баланс
</div>

<div id="balance"
class="balance">
⭐ 0
</div>

</div>


<div class="card">

<div id="username"
class="user">
Загрузка...
</div>

<div class="id">
ID: <span id="telegramId">—</span>
</div>

</div>


<div class="grid">

<button onclick="showPage('withdraw')">
💸<br>Вывод
</button>

<button onclick="showPage('referrals')">
👥<br>Рефералы
</button>

<button onclick="showPage('promo')">
🎟<br>Промокод
</button>

<button onclick="showPage('support')">
🛠<br>Поддержка
</button>

</div>

</div>


<div id="withdraw" class="page">

<header>

<div class="logo">
💸 Вывод
</div>

<div class="subtitle">
Заявка на вывод
</div>

</header>

<div class="card">

Доступно:

<div id="withdrawBalance"
class="balance">
⭐ 0
</div>

<input
id="withdrawAmount"
type="number"
placeholder="Количество Stars">

<br><br>

<button onclick="withdraw()">
💸 Создать заявку
</button>

</div>

<div id="withdrawMessage"
class="notice">

</div>

<button
onclick="showPage('home')">

← Назад

</button>

</div>


<div id="referrals" class="page">

<header>

<div class="logo">
👥 Рефералы
</div>

</header>

<div class="card">

<div>
Твоя реферальная ссылка:
</div>

<br>

<div id="refLink">
Загрузка...
</div>

<br>

<button onclick="copyReferral()">
📋 Скопировать
</button>

</div>

<button onclick="showPage('home')">
← Назад
</button>

</div>


<div id="promo" class="page">

<header>

<div class="logo">
🎟 Промокод
</div>

</header>

<div class="card">

<input
id="promoCode"
placeholder="Введите промокод">

<br><br>

<button onclick="promo()">
🎟 Активировать
</button>

</div>

<div id="promoMessage"
class="notice">

</div>

<button onclick="showPage('home')">
← Назад
</button>

</div>


<div id="support" class="page">

<header>

<div class="logo">
🛠 Поддержка
</div>

<div class="subtitle">
Сообщить о проблеме
</div>

</header>

<div class="card">

<p>
Если у тебя возникла проблема,
напиши в поддержку.
</p>

<br>

<button onclick="support()">
💬 @Eclipsed_consult
</button>

</div>

<button onclick="showPage('home')">
← Назад
</button>

</div>


</div>


<div class="bottom">

<button onclick="showPage('home')">
🏠 Главная
</button>

<button onclick="showPage('referrals')">
👥 Рефералы
</button>

<button onclick="support()">
🛠 Поддержка
</button>

</div>


<script>

const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

let userData = null;


function showPage(page) {

    document
    .querySelectorAll(".page")
    .forEach(function(element) {
        element.classList.remove("active");
    });

    document
    .getElementById(page)
    .classList.add("active");

    window.scrollTo(0, 0);
}


function openChannel() {

    tg.openTelegramLink(
        "https://t.me/eclipsedlf"
    );

}


async function checkSubscription() {

    const message =
    document.getElementById("subMessage");

    message.innerText =
    "🔄 Проверяем...";

    try {

        const response =
        await fetch(
            "/api/check-subscription",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                    "application/json"
                },
                body: JSON.stringify({
                    initData:
                    tg.initData
                })
            }
        );

        const data =
        await response.json();

        if (data.subscribed) {

            document
            .getElementById("subscribe")
            .style.display = "none";

            loadUser();

        } else {

            message.innerText =
            "❌ Сначала подпишитесь на @eclipsedlf";

        }

    } catch (error) {

        message.innerText =
        "❌ Ошибка соединения";

    }

}


async function loadUser() {

    if (!tg.initData) {

        document.getElementById(
            "username"
        ).innerText =
        "Откройте приложение через Telegram";

        return;

    }


    try {

        const response =
        await fetch(
            "/api/me",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                    "application/json"
                },
                body: JSON.stringify({
                    initData:
                    tg.initData
                })
            }
        );

        const data =
        await response.json();


        if (!data.success) {

            document
            .getElementById("subscribe")
            .style.display =
            "flex";

            return;

        }


        userData = data;


        document.getElementById(
            "username"
        ).innerText =
        data.username
        ? "@" + data.username
        : data.first_name;


        document.getElementById(
            "telegramId"
        ).innerText =
        data.telegram_id;


        updateBalance(
            data.balance
        );


        document.getElementById(
            "refLink"
        ).innerText =
        "https://t.me/GiftsUpp_bot?start=ref_" +
        data.telegram_id;

    } catch (error) {

        console.log(error);

    }

}


function updateBalance(balance) {

    const value =
    Number(balance || 0)
    .toLocaleString("ru-RU");

    document.getElementById(
        "balance"
    ).innerText =
    "⭐ " + value;

    document.getElementById(
        "withdrawBalance"
    ).innerText =
    "⭐ " + value;

}


async function withdraw() {

    const amount =
    Number(
        document.getElementById(
            "withdrawAmount"
        ).value
    );

    const message =
    document.getElementById(
        "withdrawMessage"
    );


    if (!amount || amount <= 0) {

        message.innerText =
        "❌ Укажите сумму.";

        return;

    }


    message.innerText =
    "⏳ Отправляем заявку...";


    try {

        const response =
        await fetch(
            "/api/withdraw",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                    "application/json"
                },
                body: JSON.stringify({

                    initData:
                    tg.initData,

                    amount:
                    amount

                })
            }
        );


        const data =
        await response.json();


        if (data.success) {

            message.innerText =
            "✅ Заявка отправлена!";

            updateBalance(
                data.balance
            );

        } else {

            message.innerText =
            "❌ " +
            (data.error ||
            "Ошибка");

        }

    } catch (error) {

        message.innerText =
        "❌ Сервер недоступен.";

    }

}


function copyReferral() {

    navigator.clipboard.writeText(
        document.getElementById(
            "refLink"
        ).innerText
    );

    alert("✅ Ссылка скопирована!");

}


function promo() {

    document.getElementById(
        "promoMessage"
    ).innerText =
    "ℹ️ Система промокодов пока подключается.";

}


function support() {

    tg.openTelegramLink(
        "https://t.me/Eclipsed_consult"
    );

}


loadUser();

</script>

</body>

</html>
"""


@app.route("/")
def home():
    return Response(
        HTML,
        mimetype="text/html"
    )


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
        return jsonify({
            "success": False,
            "error": "Telegram не подтверждён"
        }), 401


    user_id = int(
        user["id"]
    )

    if not is_subscribed(user_id):

        return jsonify({
            "success": False,
            "error": "Сначала подпишитесь"
        }), 403


    username = user.get(
        "username",
        ""
    )

    first_name = user.get(
        "first_name",
        ""
    )


    conn = get_db()

    row = conn.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (user_id,)
    ).fetchone()


    if not row:

        conn.execute(
            """
            INSERT INTO users
            (telegram_id, username, first_name, balance)
            VALUES (?, ?, ?, 0)
            """,
            (
                user_id,
                username,
                first_name
            )
        )

        conn.commit()


    else:

        conn.execute(
            """
            UPDATE users
            SET username = ?,
                first_name = ?
            WHERE telegram_id = ?
            """,
            (
                username,
                first_name,
                user_id
            )
        )

        conn.commit()


    row = conn.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (user_id,)
    ).fetchone()

    conn.close()


    return jsonify({

        "success": True,

        "telegram_id":
        row["telegram_id"],

        "username":
        row["username"],

        "first_name":
        row["first_name"],

        "balance":
        row["balance"]

    })


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

        return jsonify({
            "subscribed": False
        }), 401


    user_id = int(
        user["id"]
    )


    subscribed = is_subscribed(
        user_id
    )


    return jsonify({
        "subscribed": subscribed
    })


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

        return jsonify({
            "success": False,
            "error":
            "Telegram не подтверждён"
        }), 401


    user_id = int(
        user["id"]
    )


    if not is_subscribed(user_id):

        return jsonify({
            "success": False,
            "error":
            "Сначала подпишитесь"
        }), 403


    try:

        amount = float(
            data.get("amount")
        )

    except:

        return jsonify({
            "success": False,
            "error":
            "Некорректная сумма"
        }), 400


    if amount <= 0:

        return jsonify({
            "success": False,
            "error":
            "Некорректная сумма"
        }), 400


    conn = get_db()


    row = conn.execute(
        "SELECT balance FROM users WHERE telegram_id = ?",
        (user_id,)
    ).fetchone()


    if not row:

        conn.close()

        return jsonify({
            "success": False,
            "error":
            "Пользователь не найден"
        }), 404


    balance = float(
        row["balance"]
    )


    if amount > balance:

        conn.close()

        return jsonify({
            "success": False,
            "error":
            "Недостаточно Stars"
        }), 400


    username = user.get(
        "username"
    ) or user.get(
        "first_name",
        "Не указан"
    )


    if not BOT_TOKEN or not ADMIN_CHAT_ID:

        conn.close()

        return jsonify({
            "success": False,
            "error":
            "Настройки Telegram не установлены"
        }), 500


    text = (
        "💸 НОВАЯ ЗАЯВКА НА ВЫВОД\n\n"
        f"👤 Пользователь: @{username}\n"
        f"🆔 Telegram ID: {user_id}\n"
        f"⭐ Сумма: {amount:g} Stars\n"
        f"💰 Баланс: {balance:g} Stars"
    )


    try:

        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id":
                ADMIN_CHAT_ID,
                "text":
                text
            },
            timeout=15
        )

        result = response.json()

    except Exception:

        conn.close()

        return jsonify({
            "success": False,
            "error":
            "Ошибка Telegram"
        }), 500


    if not result.get("ok"):

        conn.close()

        return jsonify({
            "success": False,
            "error":
            "Telegram не принял заявку"
        }), 500


    new_balance = balance - amount


    conn.execute(
        """
        UPDATE users
        SET balance = ?
        WHERE telegram_id = ?
        """,
        (
            new_balance,
            user_id
        )
    )


    conn.commit()
    conn.close()


    return jsonify({

        "success": True,

        "balance":
        new_balance

    })


init_db()


if __name__ == "__main__":

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
