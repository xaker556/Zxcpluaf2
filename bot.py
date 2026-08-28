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


# =========================
# DATABASE
# =========================

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
            balance REAL DEFAULT 0,
            referrals INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


# =========================
# TELEGRAM DATA
# =========================

def validate_telegram_data(init_data):
    if not BOT_TOKEN or not init_data:
        return None

    try:
        data = dict(urllib.parse.parse_qsl(init_data))

        received_hash = data.pop("hash", None)

        if not received_hash:
            return None

        data_check_string = "\n".join(
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
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            calculated_hash,
            received_hash
        ):
            return None

        user = json.loads(
            data.get("user", "{}")
        )

        if not user.get("id"):
            return None

        return user

    except Exception:
        return None


# =========================
# CHECK SUBSCRIPTION
# =========================

def check_subscription(user_id):

    if not BOT_TOKEN:
        return False, "BOT_TOKEN не настроен"

    try:

        url = (
            f"https://api.telegram.org/"
            f"bot{BOT_TOKEN}/getChatMember"
        )

        response = requests.get(
            url,
            params={
                "chat_id": CHANNEL,
                "user_id": user_id
            },
            timeout=10
        )

        result = response.json()

        if not result.get("ok"):
            return False, "Не удалось проверить подписку"

        status = result["result"]["status"]

        allowed_statuses = [
            "creator",
            "administrator",
            "member"
        ]

        if status in allowed_statuses:
            return True, "Подписка подтверждена"

        return False, "Сначала подпишитесь на канал"

    except Exception:
        return False, "Ошибка проверки подписки"


# =========================
# MAIN PAGE
# =========================

HTML = r"""
<!DOCTYPE html>
<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
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
    color: #f4f0f7;

    font-family: Arial, sans-serif;

    min-height: 100vh;
}

.app {

    max-width: 430px;

    margin: auto;

    min-height: 100vh;

    padding-bottom: 90px;
}

.page {
    display: none;
}

.page.active {
    display: block;
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

.balance {

    margin: 10px 16px 20px;

    padding: 24px;

    border-radius: 20px;

    background: #1c1424;

    border: 1px solid #30223a;
}

.balance-title {

    color: #94889d;

    font-size: 13px;
}

.balance-value {

    font-size: 31px;

    font-weight: 800;

    margin-top: 8px;
}

.user-box {

    margin: 10px 16px 20px;

    display: flex;

    align-items: center;

    gap: 12px;

    background: #1c1424;

    border: 1px solid #30223a;

    padding: 15px 20px;

    border-radius: 20px;
}

.avatar {

    width: 50px;

    height: 50px;

    border-radius: 50%;

    background: #24182e;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 23px;
}

.user-name {

    font-size: 14px;

    font-weight: 700;
}

.user-status {

    color: #8d8295;

    font-size: 12px;

    margin-top: 4px;
}

.section {

    padding: 0 16px;

    margin-top: 22px;
}

.section-title {

    color: #a79aaa;

    font-size: 12px;

    font-weight: 700;

    margin-bottom: 10px;

    text-transform: uppercase;
}

.grid {

    display: grid;

    grid-template-columns: 1fr 1fr;

    gap: 10px;
}

button {

    border: 1px solid #30223a;

    background: #19121f;

    color: white;

    border-radius: 15px;

    padding: 17px 10px;

    font-size: 14px;

    cursor: pointer;
}

button:active {

    transform: scale(.98);
}

.full {

    width: 100%;
}

.back {

    margin: 0 16px 15px;

    background: #19121f;

    padding: 12px 18px;
}

.card {

    margin: 0 16px 12px;

    padding: 18px;

    border-radius: 17px;

    background: #19121f;

    border: 1px solid #30223a;
}

.card-title {

    font-size: 16px;

    font-weight: 700;

    margin-bottom: 8px;
}

.card-text {

    color: #a99dab;

    font-size: 13px;

    line-height: 1.5;
}

input {

    width: 100%;

    padding: 15px;

    margin-top: 12px;

    background: #100b16;

    border: 1px solid #3a2b44;

    border-radius: 12px;

    color: white;

    outline: none;

    font-size: 14px;
}

.action {

    width: 100%;

    margin-top: 10px;

    background: #24182e;
}

.notice {

    margin: 0 16px 15px;

    padding: 15px;

    border-radius: 14px;

    background: #1c1424;

    border: 1px solid #30223a;

    color: #a99dab;

    font-size: 13px;

    line-height: 1.5;
}

.leader {

    margin: 0 16px 10px;

    padding: 17px;

    border-radius: 15px;

    background: #19121f;

    border: 1px solid #30223a;

    display: flex;

    justify-content: space-between;
}

.bottom {

    position: fixed;

    bottom: 0;

    left: 50%;

    transform: translateX(-50%);

    width: 100%;

    max-width: 430px;

    background: #130d19;

    border-top: 1px solid #2a1d32;

    display: flex;

    padding: 10px 12px;

    gap: 10px;

    z-index: 10;
}

.bottom button {

    flex: 1;

    padding: 12px 5px;

    background: transparent;

    border: none;

    color: #9b90a3;
}

.bottom button.active {

    color: #eee7f2;

    background: #21172b;
}


/* SUBSCRIPTION */

#subscribeScreen {

    position: fixed;

    inset: 0;

    background: #100b16;

    z-index: 100;

    display: flex;

    align-items: center;

    justify-content: center;

    padding: 20px;
}

.subscribe-box {

    width: 100%;

    max-width: 390px;

    background: #19121f;

    border: 1px solid #30223a;

    border-radius: 22px;

    padding: 25px;

    text-align: center;
}

.subscribe-title {

    font-size: 24px;

    font-weight: 800;

    margin-bottom: 12px;
}

.subscribe-text {

    color: #a99dab;

    font-size: 14px;

    line-height: 1.5;

    margin-bottom: 20px;
}

</style>

</head>


<body>


<!-- SUBSCRIPTION SCREEN -->

<div id="subscribeScreen">

    <div class="subscribe-box">

        <div class="subscribe-title">
            📢 Подписка
        </div>

        <div class="subscribe-text">

            Чтобы пользоваться GiftsUpp,
            сначала подпишитесь на наш Telegram-канал.

        </div>

        <button
        class="full"
        onclick="openChannel()">

            📢 Подписаться

        </button>

        <button
        class="full"
        style="margin-top:10px"
        onclick="verifySubscription()">

            ✅ Я подписался

        </button>

        <div
        id="subscribeMessage"
        style="margin-top:15px;color:#a99dab">

        </div>

    </div>

</div>


<div class="app">


<!-- HOME -->

<div id="home" class="page active">

<header>

<div class="logo">
🎁 GiftsUpp
</div>

<div class="subtitle">
Подарки • Stars • Рефералы
</div>

</header>


<div class="balance">

<div class="balance-title">
Ваш баланс
</div>

<div
class="balance-value"
id="balance">

⭐ 0

</div>

</div>


<div class="user-box">

<div class="avatar">
🎁
</div>

<div>

<div
class="user-name"
id="username">

Загрузка...

</div>

<div class="user-status">

ID:
<span id="telegramId">
—

</span>

</div>

</div>

</div>


<div class="section">

<div class="section-title">
Аккаунт
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

<button onclick="showPage('history')">
📜<br>История
</button>

</div>

</div>


<div class="section">

<div class="section-title">
Telegram
</div>

<button
class="full"
onclick="showPage('subscription')">

📢 Проверить подписку

</button>

</div>

</div>


<!-- WITHDRAW -->

<div id="withdraw" class="page">

<header>

<div class="logo">
💸 Вывод
</div>

<div class="subtitle">
Создание заявки
</div>

</header>

<button
class="back"
onclick="showPage('home')">

← Назад

</button>


<div class="card">

<div class="card-title">
Доступно
</div>

<div
class="balance-value"
id="withdrawBalance">

⭐ 0

</div>

</div>


<div class="card">

<div class="card-title">
Сумма вывода
</div>

<div class="card-text">

Укажите количество Stars.

</div>

<input
type="number"
id="withdrawAmount"
placeholder="Например: 500"
min="1">

<button
class="action"
onclick="createWithdraw()">

💸 Создать заявку

</button>

</div>


<div
id="withdrawMessage"
class="notice">

Заявка будет отправлена администратору.

</div>

</div>


<!-- REFERRALS -->

<div id="referrals" class="page">

<header>

<div class="logo">
👥 Рефералы
</div>

<div class="subtitle">
Приглашай пользователей
</div>

</header>

<button
class="back"
onclick="showPage('home')">

← Назад

</button>


<div class="card">

<div class="card-title">
Приглашено
</div>

<div
class="balance-value"
id="referralsCount">

0

</div>

</div>


<div class="card">

<div class="card-title">
Твоя ссылка
</div>

<div
class="card-text"
id="refLink">

Загрузка...

</div>

<button
class="action"
onclick="copyReferral()">

📋 Скопировать

</button>

</div>

</div>


<!-- PROMO -->

<div id="promo" class="page">

<header>

<div class="logo">
🎟 Промокод
</div>

<div class="subtitle">
Активация промокода
</div>

</header>

<button
class="back"
onclick="showPage('home')">

← Назад

</button>


<div class="card">

<div class="card-title">
Введите промокод
</div>

<input
type="text"
id="promoCode"
placeholder="Введите код">

<button
class="action"
onclick="activatePromo()">

🎟 Активировать

</button>

</div>


<div
id="promoMessage"
class="notice">

Введите промокод.

</div>

</div>


<!-- HISTORY -->

<div id="history" class="page">

<header>

<div class="logo">
📜 История
</div>

<div class="subtitle">
Операции
</div>

</header>

<button
class="back"
onclick="showPage('home')">

← Назад

</button>


<div class="notice">

История операций будет подключена
к базе данных.

</div>

</div>


<!-- SUBSCRIPTION -->

<div id="subscription" class="page">

<header>

<div class="logo">
📢 Подписка
</div>

<div class="subtitle">
Проверка подписки
</div>

</header>

<button
class="back"
onclick="showPage('home')">

← Назад

</button>


<div class="card">

<div class="card-title">
@eclipsedlf
</div>

<div class="card-text">

Подпишись на канал и нажми
«Проверить подписку».

</div>

<button
class="action"
onclick="openChannel()">

📢 Открыть канал

</button>

<button
class="action"
onclick="verifySubscription()">

✅ Проверить подписку

</button>

</div>


<div
id="subscriptionMessage"
class="notice">

Статус пока не проверен.

</div>

</div>


<!-- LEADERS -->

<div id="leaders" class="page">

<header>

<div class="logo">
🏆 Лидерборд
</div>

<div class="subtitle">
Топ по приглашениям
</div>

</header>


<div class="leader">

<span>🥇 @username1</span>

<span>128</span>

</div>


<div class="leader">

<span>🥈 @username2</span>

<span>96</span>

</div>


<div class="leader">

<span>🥉 @username3</span>

<span>74</span>

</div>


</div>

</div>


<!-- BOTTOM -->

<div class="bottom">

<button
id="homeBtn"
class="active"
onclick="showPage('home')">

🏠<br>Главная

</button>


<button
id="leadersBtn"
onclick="showPage('leaders')">

🏆<br>Лидеры

</button>


<button
onclick="openSupport()">

🛠<br>Поддержка

</button>

</div>


<script>

const tg = window.Telegram.WebApp;

tg.ready();

tg.expand();


let currentUser = null;


/* PAGE */

function showPage(page) {

    document
    .querySelectorAll('.page')
    .forEach(p => p.classList.remove('active'));

    document
    .getElementById(page)
    .classList.add('active');

    document
    .getElementById('homeBtn')
    .classList.remove('active');

    document
    .getElementById('leadersBtn')
    .classList.remove('active');


    if (page === 'home') {

        document
        .getElementById('homeBtn')
        .classList.add('active');

    }


    if (page === 'leaders') {

        document
        .getElementById('leadersBtn')
        .classList.add('active');

    }

    window.scrollTo(0, 0);
}


/* LOAD USER */

async function loadUser() {

    if (!tg.initData) {

        document.getElementById(
            'username'
        ).innerText =
        'Откройте приложение через Telegram';

        return;

    }


    try {

        const response = await fetch(
            '/api/me',
            {

                method: 'POST',

                headers: {
                    'Content-Type':
                    'application/json'
                },

                body: JSON.stringify({

                    initData: tg.initData

                })

            }
        );


        const data =
        await response.json();


        if (!data.success) {

            return;

        }


        currentUser = data;


        document.getElementById(
            'username'
        ).innerText =
        data.username
        ? '@' + data.username
        : data.first_name;


        document.getElementById(
            'telegramId'
        ).innerText =
        data.telegram_id;


        updateBalance(
            data.balance
        );


        document.getElementById(
            'referralsCount'
        ).innerText =
        data.referrals;


        document.getElementById(
            'refLink'
        ).innerText =
        'https://t.me/GiftsUpp_bot?start=ref_' +
        data.telegram_id;


    } catch (error) {

        console.log(error);

    }

}


/* BALANCE */

function updateBalance(balance) {

    const value =
    Number(balance || 0)
    .toLocaleString('ru-RU');


    document.getElementById(
        'balance'
    ).innerText =
    '⭐ ' + value;


    document.getElementById(
        'withdrawBalance'
    ).innerText =
    '⭐ ' + value;

}


/* SUBSCRIPTION */

async function verifySubscription() {

    const message =
    document.getElementById(
        'subscribeMessage'
    );


    message.innerText =
    '🔄 Проверяем подписку...';


    try {

        const response =
        await fetch(
            '/api/check-subscription',
            {

                method: 'POST',

                headers: {
                    'Content-Type':
                    'application/json'
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

            document.getElementById(
                'subscribeScreen'
            ).style.display =
            'none';


            document.getElementById(
                'subscriptionMessage'
            ).innerText =
            '✅ Подписка подтверждена!';

        } else {

            message.innerText =
            '❌ Сначала подпишитесь на @eclipsedlf';

        }


    } catch (error) {

        message.innerText =
        '❌ Ошибка проверки.';

    }

}


/* OPEN CHANNEL */

function openChannel() {

    tg.openTelegramLink(
        'https://t.me/eclipsedlf'
    );

}


/* WITHDRAW */

async function createWithdraw() {

    const amount =
    Number(
        document.getElementById(
            'withdrawAmount'
        ).value
    );


    const message =
    document.getElementById(
        'withdrawMessage'
    );


    if (!amount || amount <= 0) {

        message.innerText =
        '❌ Укажите корректную сумму.';

        return;

    }


    message.innerText =
    '⏳ Отправляем заявку...';


    try {

        const response =
        await fetch(
            '/api/withdraw',
            {

                method: 'POST',

                headers: {
                    'Content-Type':
                    'application/json'
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
            '✅ Заявка отправлена администратору!';

            updateBalance(
                data.balance
            );

        } else {

            message.innerText =
            '❌ ' +
            (data.error ||
            'Ошибка.');

        }


    } catch (error) {

        message.innerText =
        '❌ Сервер недоступен.';

    }

}


/* REFERRAL */

function copyReferral() {

    navigator.clipboard.writeText(
        document.getElementById(
            'refLink'
        ).innerText
    );


    alert(
        '✅ Ссылка скопирована!'
    );

}


/* PROMO */

function activatePromo() {

    const code =
    document.getElementById(
        'promoCode'
    ).value.trim();


    if (!code) {

        document.getElementById(
            'promoMessage'
        ).innerText =
        '❌ Введите промокод.';

        return;

    }


    document.getElementById(
        'promoMessage'
    ).innerText =
    'ℹ️ Промокоды подключим к базе данных.';

}


/* SUPPORT */

function openSupport() {

    tg.openTelegramLink(
        'https://t.me/Eclipsed_consult'
    );

}


/* START */

async function startApp() {

    await loadUser();

    await verifySubscription();

}


startApp();

</script>

</body>

</html>
"""


# =========================
# ROUTES
# =========================

@app.route("/")
def home():

    return Response(
        HTML,
        mimetype="text/html"
    )


@app.route("/api/me", methods=["POST"])
def api_me():

    data = request.get_json(
        silent=True
    ) or {}

    user = validate_telegram_data(
        data.get("initData")
    )

    if not user:

        return jsonify({
            "success": False,
            "error": "Telegram пользователь не подтверждён"
        }), 401


    telegram_id = int(
        user["id"]
    )

    username = user.get(
        "username",
        ""
    )

    first_name = user.get(
        "first_name",
        ""
    )


    subscribed, _ = check_subscription(
        telegram_id
    )


    if not subscribed:

        return jsonify({
            "success": False,
            "error": "Сначала подпишитесь на канал"
        }), 403


    conn = get_db()


    row = conn.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,)
    ).fetchone()


    if not row:

        conn.execute(
            """
            INSERT INTO users
            (
                telegram_id,
                username,
                first_name,
                balance,
                referrals
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                username,
                first_name,
                0,
                0
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
                telegram_id
            )
        )

        conn.commit()


    row = conn.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,)
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
        row["balance"],

        "referrals":
        row["referrals"]

    })


@app.route(
    "/api/check-subscription",
    methods=["POST"]
)
def api_check_subscription():

    data = request.get_json(
        silent=True
    ) or {}


    user = validate_telegram_data(
        data.get("initData")
    )


    if not user:

        return jsonify({
            "subscribed": False,
            "error": "Пользователь не подтверждён"
        }), 401


    user_id = int(
        user["id"]
    )


    subscribed, message = \
        check_subscription(
            user_id
        )


    return jsonify({

        "subscribed":
        subscribed,

        "message":
        message

    })


@app.route(
    "/api/withdraw",
    methods=["POST"]
)
def api_withdraw():

    data = request.get_json(
        silent=True
    ) or {}


    user = validate_telegram_data(
        data.get("initData")
    )


    if not user:

        return jsonify({
            "success": False,
            "error": "Пользователь не подтверждён"
        }), 401


    user_id = int(
        user["id"]
    )


    subscribed, _ = \
        check_subscription(
            user_id
        )


    if not subscribed:

        return jsonify({
            "success": False,
            "error": "Сначала подпишитесь на канал"
        }), 403


    try:

        amount = float(
            data.get("amount")
        )

    except:

        return jsonify({
            "success": False,
            "error": "Некорректная сумма"
        }), 400


    if amount <= 0:

        return jsonify({
            "success": False,
            "error": "Некорректная сумма"
        }), 400


    conn = get_db()


    row = conn.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,)
    ).fetchone()


    if not row:

        conn.close()

        return jsonify({
            "success": False,
            "error": "Пользователь не найден"
        }), 404


    balance = float(
        row["balance"]
    )


    if amount > balance:

        conn.close()

        return jsonify({
            "success": False,
            "error": "Недостаточно Stars"
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
            "error": "Telegram настройки не установлены"
        }), 500


    text = (

        "💸 НОВАЯ ЗАЯВКА НА ВЫВОД\n\n"

        f"👤 Пользователь: @{username}\n"

        f"🆔 Telegram ID: {user_id}\n"

        f"⭐ Сумма: {amount:g} Stars\n"

        f"💰 Баланс: {balance:g} Stars\n\n"

        "📌 Статус: Новая заявка"

    )


    try:

        response = requests.post(

            f"https://api.telegram.org/"
            f"bot{BOT_TOKEN}/sendMessage",

            json={

                "chat_id":
                ADMIN_CHAT_ID,

                "text":
                text

            },

            timeout=15

        )


        result =
        response.json()


    except Exception:

        conn.close()

        return jsonify({
            "success": False,
            "error": "Ошибка соединения с Telegram"
        }), 500


    if not result.get("ok"):

        conn.close()

        return jsonify({
            "success": False,
            "error": "Telegram не принял заявку"
        }), 500


    new_balance = \
        balance - amount


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

        "message":
        "Заявка отправлена",

        "balance":
        new_balance

    })


# =========================
# START
# =========================

init_db()


if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
  )
