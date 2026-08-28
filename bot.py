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
BOT_USERNAME = os.getenv("BOT_USERNAME", "GiftsUpp_bot")
CHANNEL = "@eclipsedlf"

DB_FILE = "giftsupp.db"
WEBAPP_URL = "https://zxcpluaf2.onrender.com"


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
            referrals INTEGER DEFAULT 0,
            referred_by INTEGER,
            created_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)

    conn.commit()
    conn.close()


def telegram_user(init_data):
    if not BOT_TOKEN or not init_data:
        return None

    try:
        data = dict(
            urllib.parse.parse_qsl(init_data)
        )

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
            data.get("user", "{}")
        )

        if not user.get("id"):
            return None

        return user

    except Exception:
        return None


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


def upsert_user(user, referrer_id=None):
    uid = int(user["id"])

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
        """
        SELECT *
        FROM users
        WHERE telegram_id=?
        """,
        (uid,)
    ).fetchone()

    if row is None:

        valid_ref = None

        if referrer_id and referrer_id != uid:

            ref = conn.execute(
                """
                SELECT telegram_id
                FROM users
                WHERE telegram_id=?
                """,
                (referrer_id,)
            ).fetchone()

            if ref:
                valid_ref = referrer_id

        conn.execute(
            """
            INSERT INTO users (
                telegram_id,
                username,
                first_name,
                referred_by
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                uid,
                username,
                first_name,
                valid_ref
            )
        )

        if valid_ref:

            conn.execute(
                """
                UPDATE users
                SET referrals = referrals + 1
                WHERE telegram_id=?
                """,
                (valid_ref,)
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
                uid
            )
        )

    conn.commit()

    row = conn.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id=?
        """,
        (uid,)
    ).fetchone()

    conn.close()

    return row


HTML = r"""
<!doctype html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width,initial-scale=1">

<title>GiftsUpp</title>

<script src="https://telegram.org/js/telegram-web-app.js"></script>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
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
    padding: 26px 18px 16px;
}

.logo {
    font-size: 26px;
    font-weight: 800;
}

.sub {
    color: #93899b;
    font-size: 13px;
    margin-top: 5px;
}

.card {
    margin: 12px 16px;
    padding: 19px;
    background: #19121f;
    border: 1px solid #30223a;
    border-radius: 18px;
}

.balance {
    font-size: 32px;
    font-weight: 800;
    margin-top: 7px;
}

.id {
    color: #93899b;
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
    padding: 15px 10px;
    border: 1px solid #30223a;
    border-radius: 14px;
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
    padding: 9px;
    display: flex;
    gap: 8px;
    background: #130d19;
    border-top: 1px solid #2a1d32;
}

.notice {
    margin: 12px 16px;
    padding: 14px;
    background: #1c1424;
    border-radius: 14px;
    color: #aaa;
    font-size: 13px;
}

.leader {
    display: flex;
    justify-content: space-between;
    margin: 8px 16px;
    padding: 15px;
    background: #19121f;
    border: 1px solid #30223a;
    border-radius: 14px;
}

#subscribe {
    position: fixed;
    inset: 0;
    background: #100b16;
    z-index: 20;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.box {
    background: #19121f;
    border: 1px solid #30223a;
    border-radius: 20px;
    padding: 24px;
    text-align: center;
}

</style>

</head>

<body>

<div id="subscribe">

    <div class="box">

        <h2>📢 Подписка</h2>

        <p>
            Сначала подпишитесь на
            @eclipsedlf.
        </p>

        <button onclick="openChannel()">
            📢 Подписаться
        </button>

        <br><br>

        <button onclick="checkSub()">
            ✅ Я подписался
        </button>

        <p id="subMsg"></p>

    </div>

</div>


<div class="app">


<div id="home" class="page active">

<header>

<div class="logo">
🎁 GiftsUpp
</div>

<div class="sub">
Подарки • Stars • Рефералы
</div>

</header>


<div class="card">

<div class="sub">
Ваш баланс
</div>

<div id="balance" class="balance">
⭐ 0
</div>

</div>


<div class="card">

<div id="username">
Загрузка...
</div>

<div class="id">
ID:
<span id="uid">—</span>
</div>

</div>


<div class="grid">

<button onclick="show('withdraw')">
💸<br>Вывод
</button>

<button onclick="show('referrals')">
👥<br>Рефералы
</button>

<button onclick="show('leaders')">
🏆<br>Лидеры
</button>

<button onclick="show('promo')">
🎟<br>Промокод
</button>

</div>

</div>


<div id="withdraw" class="page">

<header>

<div class="logo">
💸 Вывод
</div>

<div class="sub">
Заявка на вывод
</div>

</header>


<div class="card">

Доступно:

<div id="wbalance" class="balance">
⭐ 0
</div>

<input
id="amount"
type="number"
min="1"
placeholder="Количество Stars">

<br><br>

<button onclick="withdraw()">
💸 Создать заявку
</button>

</div>


<div id="wmsg" class="notice"></div>


<button onclick="show('home')">
← Назад
</button>

</div>


<div id="referrals" class="page">

<header>

<div class="logo">
👥 Рефералы
</div>

<div class="sub">
Приглашённые пользователи
</div>

</header>


<div class="card">

Приглашено:

<b id="refcount">
0
</b>

<br><br>

<div id="reflink">
Загрузка...
</div>

<br>

<button onclick="copyRef()">
📋 Скопировать ссылку
</button>

</div>


<div class="notice">

Пользователь засчитывается один раз
при первом входе по реферальной ссылке.

</div>


<button onclick="show('home')">
← Назад
</button>

</div>


<div id="leaders" class="page">

<header>

<div class="logo">
🏆 Лидеры
</div>

<div class="sub">
Топ пользователей по приглашениям
</div>

</header>


<div id="leadersList">

<div class="notice">
Загрузка...
</div>

</div>


<button onclick="show('home')">
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


<div id="pmsg" class="notice"></div>


<button onclick="show('home')">
← Назад
</button>

</div>


</div>


<div class="bottom">

<button onclick="show('home')">
🏠 Главная
</button>

<button onclick="show('leaders')">
🏆 Лидеры
</button>

<button onclick="support()">
🛠 Поддержка
</button>

</div>


<script>

const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

let data = null;


function show(id) {

    document
    .querySelectorAll(".page")
    .forEach(function(x) {
        x.classList.remove("active");
    });

    document
    .getElementById(id)
    .classList.add("active");

    if (id === "leaders") {
        loadLeaders();
    }

    window.scrollTo(0, 0);
}


function openChannel() {

    tg.openTelegramLink(
        "https://t.me/eclipsedlf"
    );

}


async function checkSub() {

    const message =
    document.getElementById("subMsg");

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

        const result =
        await response.json();

        if (result.subscribed) {

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


function setBalance(value) {

    const formatted =
    Number(value || 0)
    .toLocaleString("ru-RU");

    document.getElementById(
        "balance"
    ).innerText =
    "⭐ " + formatted;

    document.getElementById(
        "wbalance"
    ).innerText =
    "⭐ " + formatted;

}


async function loadUser() {

    if (!tg.initData) {

        document.getElementById(
            "username"
        ).innerText =
        "Откройте приложение через Telegram";

        return;

    }

    const params =
    new URLSearchParams(
        window.location.search
    );

    const referrerId =
    params.get("ref");


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
                    tg.initData,

                    referrer_id:
                    referrerId

                })
            }
        );

        const result =
        await response.json();

        if (!result.success) {

            document
            .getElementById("subscribe")
            .style.display = "flex";

            return;

        }

        data = result;

        document.getElementById(
            "username"
        ).innerText =
        result.username
        ? "@" + result.username
        : result.first_name;

        document.getElementById(
            "uid"
        ).innerText =
        result.telegram_id;

        setBalance(
            result.balance
        );

        document.getElementById(
            "refcount"
        ).innerText =
        result.referrals;

        document.getElementById(
            "reflink"
        ).innerText =
        result.ref_link;

    } catch (error) {

        console.log(error);

    }

}


async function withdraw() {

    const amount =
    Number(
        document.getElementById(
            "amount"
        ).value
    );

    const message =
    document.getElementById("wmsg");

    if (!amount || amount <= 0) {

        message.innerText =
        "❌ Укажите сумму.";

        return;

    }

    message.innerText =
    "⏳ Отправляем...";

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

        const result =
        await response.json();

        if (result.success) {

            message.innerText =
            "✅ Заявка отправлена!";

            setBalance(
                result.balance
            );

        } else {

            message.innerText =
            "❌ " +
            (
                result.error ||
                "Ошибка"
            );

        }

    } catch (error) {

        message.innerText =
        "❌ Сервер недоступен.";

    }

}


function copyRef() {

    navigator.clipboard.writeText(
        document.getElementById(
            "reflink"
        ).innerText
    );

    alert(
        "✅ Ссылка скопирована"
    );

}


async function loadLeaders() {

    const box =
    document.getElementById(
        "leadersList"
    );

    box.innerHTML =
    '<div class="notice">🔄 Загрузка...</div>';

    try {

        const response =
        await fetch(
            "/api/leaders"
        );

        const result =
        await response.json();

        if (!result.success) {

            box.innerHTML =
            '<div class="notice">❌ Ошибка</div>';

            return;

        }

        if (!result.leaders.length) {

            box.innerHTML =
            '<div class="notice">Пока нет участников.</div>';

            return;

        }

        box.innerHTML =
        result.leaders.map(
            function(user, index) {

                let medal =
                ["🥇", "🥈", "🥉"][index]
                ||
                (index + 1) + ".";

                return `
                <div class="leader">
                    <span>
                        ${medal} ${escapeHtml(user.name)}
                    </span>

                    <b>
                        ${user.referrals}
                    </b>
                </div>
                `;

            }
        ).join("");

    } catch (error) {

        box.innerHTML =
        '<div class="notice">❌ Ошибка загрузки</div>';

    }

}


function escapeHtml(text) {

    return String(text).replace(
        /[&<>"']/g,
        function(char) {

            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#039;"
            }[char];

        }
    );

}


function promo() {

    document.getElementById(
        "pmsg"
    ).innerText =
    "ℹ️ Промокоды пока не подключены.";

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

        return jsonify(
            success=False,
            error="Telegram не подтверждён"
        ), 401

    uid = int(user["id"])

    if not is_subscribed(uid):

        return jsonify(
            success=False,
            error="Сначала подпишитесь"
        ), 403

    referrer_id = data.get(
        "referrer_id"
    )

    try:

        referrer_id = (
            int(referrer_id)
            if referrer_id
            else None
        )

    except (TypeError, ValueError):

        referrer_id = None

    row = upsert_user(
        user,
        referrer_id
    )

    return jsonify(
        success=True,
        telegram_id=row["telegram_id"],
        username=row["username"],
        first_name=row["first_name"],
        balance=row["balance"],
        referrals=row["referrals"],

        ref_link=(
            f"{WEBAPP_URL}"
            f"/?ref={uid}"
        )
    )


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


@app.route("/api/leaders")
def api_leaders():

    conn = get_db()

    rows = conn.execute(
        """
        SELECT username, first_name, referrals
        FROM users
        WHERE referrals > 0
        ORDER BY referrals DESC, created_at ASC
        LIMIT 20
        """
    ).fetchall()

    conn.close()

    leaders = []

    for row in rows:

        if row["username"]:
            name = "@" + row["username"]
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

    uid = int(user["id"])

    if not is_subscribed(uid):

        return jsonify(
            success=False,
            error="Сначала подпишитесь"
        ), 403

    try:

        amount = float(
            data.get("amount")
        )

    except (TypeError, ValueError):

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

    name = (
        user.get("username")
        or user.get("first_name")
        or "Не указан"
    )

    text = (
        "💸 НОВАЯ ЗАЯВКА НА ВЫВОД\n\n"
        f"👤 Пользователь: @{name}\n"
        f"🆔 Telegram ID: {uid}\n"
        f"⭐ Сумма: {amount:g} Stars\n"
        f"💰 Баланс: {balance:g} Stars"
    )

    try:

        response = requests.post(
            f"https://api.telegram.org/"
            f"bot{BOT_TOKEN}/sendMessage",

            json={
                "chat_id": ADMIN_CHAT_ID,
                "text": text
            },

            timeout=15
        )

        result = response.json()

    except Exception:

        conn.close()

        return jsonify(
            success=False,
            error="Ошибка Telegram"
        ), 500

    if not result.get("ok"):

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
