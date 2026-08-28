import os
import sqlite3
import json
import hmac
import hashlib
import urllib.parse
import requests

from flask import Flask, request, jsonify, Response

app = Flask(__name__)

# ============================================================
# НАСТРОЙКИ
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()

# Username бота БЕЗ @
BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    "GiftsUpp_bot"
).strip().lstrip("@")

# Канал
CHANNEL = os.getenv(
    "CHANNEL",
    "@eclipsedlf"
).strip()

# Ссылка на Mini App
WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    "https://zxcpluaf2.onrender.com"
).strip().rstrip("/")

DB_FILE = "giftsupp.db"


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(
        DB_FILE,
        timeout=20
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

            created_at INTEGER
                DEFAULT (strftime('%s','now'))

        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# TELEGRAM WEB APP VALIDATION
# ============================================================

def telegram_user(init_data):

    if not BOT_TOKEN:
        return None

    if not init_data:
        return None

    try:

        data = dict(
            urllib.parse.parse_qsl(
                init_data,
                keep_blank_values=True
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
            BOT_TOKEN.encode("utf-8"),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            check_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            calculated_hash,
            received_hash
        ):
            return None

        user_json = data.get(
            "user",
            "{}"
        )

        user = json.loads(
            user_json
        )

        if not user.get("id"):
            return None

        return user

    except Exception as e:

        print(
            "telegram_user error:",
            e
        )

        return None


# ============================================================
# SUBSCRIPTION CHECK
# ============================================================

def is_subscribed(user_id):

    if not BOT_TOKEN:
        print(
            "BOT_TOKEN не установлен"
        )

        return False

    try:

        response = requests.get(
            "https://api.telegram.org/"
            f"bot{BOT_TOKEN}/getChatMember",

            params={
                "chat_id": CHANNEL,
                "user_id": user_id
            },

            timeout=10
        )

        result = response.json()

        print(
            "Subscription check:",
            result
        )

        if not result.get("ok"):
            return False

        status = result["result"].get(
            "status"
        )

        return status in (
            "member",
            "administrator",
            "creator"
        )

    except Exception as e:

        print(
            "Subscription error:",
            e
        )

        return False


# ============================================================
# USER / REFERRALS
# ============================================================

def upsert_user(
    user,
    referrer_id=None
):

    uid = int(
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

    conn = get_db()

    existing = conn.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
        (uid,)
    ).fetchone()

    # --------------------------------------------------------
    # НОВЫЙ ПОЛЬЗОВАТЕЛЬ
    # --------------------------------------------------------

    if existing is None:

        valid_referrer = None

        if (
            referrer_id
            and int(referrer_id) != uid
        ):

            referrer = conn.execute(
                """
                SELECT telegram_id
                FROM users
                WHERE telegram_id = ?
                """,
                (int(referrer_id),)
            ).fetchone()

            if referrer:

                valid_referrer = int(
                    referrer_id
                )

        # Создаём пользователя
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
                valid_referrer
            )
        )

        # Засчитываем реферала
        if valid_referrer:

            conn.execute(
                """
                UPDATE users
                SET referrals = referrals + 1
                WHERE telegram_id = ?
                """,
                (
                    valid_referrer,
                )
            )

            print(
                f"REFERRAL: "
                f"{uid} приглашён "
                f"пользователем "
                f"{valid_referrer}"
            )

    # --------------------------------------------------------
    # СУЩЕСТВУЮЩИЙ ПОЛЬЗОВАТЕЛЬ
    # --------------------------------------------------------

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
                uid
            )
        )

        print(
            f"Existing user: {uid}"
        )

    conn.commit()

    row = conn.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
        (uid,)
    ).fetchone()

    conn.close()

    return row


# ============================================================
# HTML MINI APP
# ============================================================

HTML = r"""
<!doctype html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1"
>

<title>GiftsUpp</title>

<script
    src="https://telegram.org/js/telegram-web-app.js">
</script>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    background:
        #100b16;

    color: white;

    font-family:
        Arial,
        sans-serif;

}

.app {

    max-width: 430px;

    margin: auto;

    min-height: 100vh;

    padding-bottom: 100px;

}

header {

    padding:
        26px
        18px
        16px;

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

    margin:
        12px 16px;

    padding: 19px;

    background:
        #19121f;

    border:
        1px solid #30223a;

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

    grid-template-columns:
        1fr 1fr;

    gap: 10px;

    margin: 16px;

}

button {

    width: 100%;

    padding: 15px 10px;

    border:
        1px solid #30223a;

    border-radius: 14px;

    background:
        #21172b;

    color: white;

    font-size: 14px;

    cursor: pointer;

}

button:active {

    transform: scale(.98);

}

input {

    width: 100%;

    padding: 14px;

    margin-top: 10px;

    background:
        #100b16;

    border:
        1px solid #3a2b44;

    border-radius: 12px;

    color: white;

    outline: none;

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

    transform:
        translateX(-50%);

    width: 100%;

    max-width: 430px;

    padding: 9px;

    display: flex;

    gap: 8px;

    background:
        #130d19;

    border-top:
        1px solid #2a1d32;

    z-index: 10;

}

.notice {

    margin:
        12px 16px;

    padding: 14px;

    background:
        #1c1424;

    border-radius: 14px;

    color: #aaa;

    font-size: 13px;

}

.leader {

    display: flex;

    justify-content:
        space-between;

    align-items:
        center;

    margin:
        8px 16px;

    padding: 15px;

    background:
        #19121f;

    border:
        1px solid #30223a;

    border-radius: 14px;

}

.refbox {

    word-break: break-all;

    color: #cdb9dc;

    font-size: 12px;

    line-height: 1.5;

}

#subscribe {

    position: fixed;

    inset: 0;

    background:
        #100b16;

    z-index: 20;

    display: none;

    align-items:
        center;

    justify-content:
        center;

    padding: 20px;

}

.box {

    width: 100%;

    max-width: 360px;

    background:
        #19121f;

    border:
        1px solid #30223a;

    border-radius: 20px;

    padding: 24px;

    text-align: center;

}

</style>

</head>

<body>


<!-- =======================================================
     SUBSCRIPTION
======================================================= -->

<div id="subscribe">

    <div class="box">

        <h2>
            📢 Подписка
        </h2>

        <p>
            Чтобы пользоваться
            GiftsUpp, подпишитесь
            на канал @eclipsedlf.
        </p>

        <button
            onclick="openChannel()"
        >
            📢 Подписаться
        </button>

        <br><br>

        <button
            onclick="checkSub()"
        >
            ✅ Я подписался
        </button>

        <p id="subMsg"></p>

    </div>

</div>


<div class="app">


<!-- =======================================================
     HOME
======================================================= -->

<div
    id="home"
    class="page active"
>

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

    <div
        id="balance"
        class="balance"
    >
        ⭐ 0
    </div>

</div>


<div class="card">

    <div id="username">
        Загрузка...
    </div>

    <div class="id">

        ID:
        <span id="uid">
            —
        </span>

    </div>

</div>


<div class="grid">

    <button
        onclick="show('withdraw')"
    >
        💸<br>
        Вывод
    </button>

    <button
        onclick="show('referrals')"
    >
        👥<br>
        Рефералы
    </button>

    <button
        onclick="show('leaders')"
    >
        🏆<br>
        Лидеры
    </button>

    <button
        onclick="show('promo')"
    >
        🎟<br>
        Промокод
    </button>

</div>

</div>


<!-- =======================================================
     WITHDRAW
======================================================= -->

<div
    id="withdraw"
    class="page"
>

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

    <div
        id="wbalance"
        class="balance"
    >
        ⭐ 0
    </div>

    <input
        id="amount"
        type="number"
        min="1"
        placeholder="Количество Stars"
    >

    <br><br>

    <button
        onclick="withdraw()"
    >
        💸 Создать заявку
    </button>

</div>


<div
    id="wmsg"
    class="notice"
></div>


<button
    onclick="show('home')"
>
    ← Назад
</button>

</div>


<!-- =======================================================
     REFERRALS
======================================================= -->

<div
    id="referrals"
    class="page"
>

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

    <div class="sub">
        Ваша реферальная ссылка:
    </div>

    <div
        id="reflink"
        class="refbox"
    >
        Загрузка...
    </div>

    <br>

    <button
        onclick="copyRef()"
    >
        📋 Скопировать ссылку
    </button>

    <br><br>

    <button
        onclick="shareRef()"
    >
        📤 Пригласить друзей
    </button>

</div>


<div class="notice">

    Реферал засчитывается
    автоматически при первом
    запуске приложения по вашей
    ссылке.

</div>


<button
    onclick="show('home')"
>
    ← Назад
</button>

</div>


<!-- =======================================================
     LEADERS
======================================================= -->

<div
    id="leaders"
    class="page"
>

<header>

    <div class="logo">
        🏆 Лидеры
    </div>

    <div class="sub">
        Топ пользователей
        по приглашениям
    </div>

</header>


<div id="leadersList">

    <div class="notice">
        Загрузка...
    </div>

</div>


<button
    onclick="show('home')"
>
    ← Назад
</button>

</div>


<!-- =======================================================
     PROMO
======================================================= -->

<div
    id="promo"
    class="page"
>

<header>

    <div class="logo">
        🎟 Промокод
    </div>

</header>


<div class="card">

    <input
        id="promoCode"
        placeholder="Введите промокод"
    >

    <br><br>

    <button
        onclick="promo()"
    >
        🎟 Активировать
    </button>

</div>


<div
    id="pmsg"
    class="notice"
></div>


<button
    onclick="show('home')"
>
    ← Назад
</button>

</div>


</div>


<!-- =======================================================
     BOTTOM MENU
======================================================= -->

<div class="bottom">

    <button
        onclick="show('home')"
    >
        🏠 Главная
    </button>

    <button
        onclick="show('leaders')"
    >
        🏆 Лидеры
    </button>

    <button
        onclick="support()"
    >
        🛠 Поддержка
    </button>

</div>


<script>

// ==========================================================
// TELEGRAM
// ==========================================================

const tg =
    window.Telegram.WebApp;

tg.ready();
tg.expand();

let data = null;


// ==========================================================
// PAGE SWITCH
// ==========================================================

function show(id) {

    document
        .querySelectorAll(".page")
        .forEach(function(page) {

            page.classList.remove(
                "active"
            );

        });

    const target =
        document.getElementById(id);

    if (target) {

        target.classList.add(
            "active"
        );

    }

    if (id === "leaders") {

        loadLeaders();

    }

    window.scrollTo(
        0,
        0
    );
}


// ==========================================================
// CHANNEL
// ==========================================================

function openChannel() {

    tg.openTelegramLink(
        "https://t.me/eclipsedlf"
    );

}


// ==========================================================
// CHECK SUBSCRIPTION
// ==========================================================

async function checkSub() {

    const message =
        document.getElementById(
            "subMsg"
        );

    message.innerText =
        "🔄 Проверяем подписку...";

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

                    body:
                        JSON.stringify({
                            initData:
                                tg.initData
                        })
                }
            );

        const result =
            await response.json();

        if (
            result.subscribed
        ) {

            document
                .getElementById(
                    "subscribe"
                )
                .style.display =
                    "none";

            loadUser();

        } else {

            message.innerText =
                "❌ Подписка не найдена. " +
                "Подпишитесь на @eclipsedlf " +
                "и нажмите кнопку ещё раз.";

        }

    } catch (error) {

        console.log(error);

        message.innerText =
            "❌ Ошибка соединения.";

    }

}


// ==========================================================
// BALANCE
// ==========================================================

function setBalance(value) {

    const formatted =
        Number(
            value || 0
        ).toLocaleString(
            "ru-RU"
        );

    document
        .getElementById(
            "balance"
        )
        .innerText =
            "⭐ " + formatted;

    document
        .getElementById(
            "wbalance"
        )
        .innerText =
            "⭐ " + formatted;
}


// ==========================================================
// GET REFERRER FROM TELEGRAM MINI APP
// ==========================================================

function getReferrerId() {

    try {

        const startParam =
            tg.initDataUnsafe
                ?.start_param;

        if (!startParam) {

            return null;

        }

        if (
            startParam.startsWith(
                "ref_"
            )
        ) {

            const id =
                startParam.substring(
                    4
                );

            if (
                /^\d+$/.test(id)
            ) {

                return id;

            }

        }

    } catch (error) {

        console.log(
            "Referral parse error:",
            error
        );

    }

    return null;
}


// ==========================================================
// LOAD USER
// ==========================================================

async function loadUser() {

    if (!tg.initData) {

        document
            .getElementById(
                "username"
            )
            .innerText =
                "Откройте приложение через Telegram";

        return;

    }

    // ВАЖНО:
    // Получаем реферала именно
    // из Telegram start_param

    const referrerId =
        getReferrerId();

    console.log(
        "Referral ID:",
        referrerId
    );

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

                    body:
                        JSON.stringify({

                            initData:
                                tg.initData,

                            referrer_id:
                                referrerId

                        })
                }
            );

        const result =
            await response.json();

        console.log(
            "ME:",
            result
        );

        if (!result.success) {

            if (
                response.status === 403
            ) {

                document
                    .getElementById(
                        "subscribe"
                    )
                    .style.display =
                        "flex";

                return;

            }

            document
                .getElementById(
                    "username"
                )
                .innerText =
                    result.error ||
                    "Ошибка";

            return;

        }

        data = result;


        document
            .getElementById(
                "username"
            )
            .innerText =
                result.username
                ? "@" +
                    result.username
                : (
                    result.first_name ||
                    "Пользователь"
                );


        document
            .getElementById(
                "uid"
            )
            .innerText =
                result.telegram_id;


        setBalance(
            result.balance
        );


        document
            .getElementById(
                "refcount"
            )
            .innerText =
                result.referrals;


        document
            .getElementById(
                "reflink"
            )
            .innerText =
                result.ref_link;


    } catch (error) {

        console.log(
            "loadUser error:",
            error
        );

        document
            .getElementById(
                "username"
            )
            .innerText =
                "❌ Ошибка загрузки";

    }

}


// ==========================================================
// COPY REFERRAL
// ==========================================================

function copyRef() {

    const link =
        document
            .getElementById(
                "reflink"
            )
            .innerText;

    if (!link) {

        return;

    }

    navigator.clipboard
        .writeText(link)
        .then(
            function() {

                alert(
                    "✅ Ссылка скопирована"
                );

            }
        )
        .catch(
            function() {

                alert(
                    "Скопируйте ссылку вручную:\n" +
                    link
                );

            }
        );

}


// ==========================================================
// SHARE REFERRAL
// ==========================================================

function shareRef() {

    const link =
        document
            .getElementById(
                "reflink"
            )
            .innerText;

    if (!link) {

        return;

    }

    const text =
        "🎁 Заходи в GiftsUpp!";

    const shareUrl =
        "https://t.me/share/url" +
        "?url=" +
        encodeURIComponent(link) +
        "&text=" +
        encodeURIComponent(text);

    tg.openTelegramLink(
        shareUrl
    );

}


// ==========================================================
// WITHDRAW
// ==========================================================

async function withdraw() {

    const amount =
        Number(
            document
                .getElementById(
                    "amount"
                )
                .value
        );

    const message =
        document
            .getElementById(
                "wmsg"
            );


    if (
        !amount ||
        amount <= 0
    ) {

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

                    body:
                        JSON.stringify({

                            initData:
                                tg.initData,

                            amount:
                                amount

                        })
                }
            );


        const result =
            await response.json();


        if (
            result.success
        ) {

            message.innerText =
                "✅ Заявка отправлена!";

            setBalance(
                result.balance
            );

            document
                .getElementById(
                    "amount"
                )
                .value = "";


        } else {

            message.innerText =
                "❌ " +
                (
                    result.error ||
                    "Ошибка"
                );

        }


    } catch (error) {

        console.log(error);

        message.innerText =
            "❌ Сервер недоступен.";

    }

}


// ==========================================================
// LEADERS
// ==========================================================

async function loadLeaders() {

    const box =
        document
            .getElementById(
                "leadersList"
            );

    box.innerHTML =
        '<div class="notice">' +
        '🔄 Загрузка...' +
        '</div>';


    try {

        const response =
            await fetch(
                "/api/leaders"
            );

        const result =
            await response.json();


        if (
            !result.success
        ) {

            box.innerHTML =
                '<div class="notice">' +
                '❌ Ошибка' +
                '</div>';

            return;

        }


        if (
            !result.leaders.length
        ) {

            box.innerHTML =
                '<div class="notice">' +
                'Пока нет участников.' +
                '</div>';

            return;

        }


        box.innerHTML =
            result.leaders
                .map(
                    function(
                        user,
                        index
                    ) {

                        const medals =
                            [
                                "🥇",
                                "🥈",
                                "🥉"
                            ];

                        const medal =
                            medals[index] ||
                            (
                                index + 1
                            ) + ".";


                        return `
                        <div class="leader">

                            <span>
                                ${medal}
                                ${escapeHtml(
                                    user.name
                                )}
                            </span>

                            <b>
                                ${user.referrals}
                                👥
                            </b>

                        </div>
                        `;

                    }
                )
                .join("");


    } catch (error) {

        console.log(error);

        box.innerHTML =
            '<div class="notice">' +
            '❌ Ошибка загрузки' +
            '</div>';

    }

}


// ==========================================================
// HTML ESCAPE
// ==========================================================

function escapeHtml(text) {

    return String(
        text
    ).replace(
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


// ==========================================================
// PROMO
// ==========================================================

function promo() {

    document
        .getElementById(
            "pmsg"
        )
        .innerText =
            "ℹ️ Промокоды пока не подключены.";

}


// ==========================================================
// SUPPORT
// ==========================================================

function support() {

    tg.openTelegramLink(
        "https://t.me/Eclipsed_consult"
    );

}


// ==========================================================
// START
// ==========================================================

loadUser();

</script>

</body>

</html>
"""


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return Response(
        HTML,
        mimetype="text/html"
    )


# ============================================================
# API ME
# ============================================================

@app.route(
    "/api/me",
    methods=["POST"]
)
def api_me():

    data = request.get_json(
        silent=True
    ) or {}

    init_data = data.get(
        "initData"
    )

    user = telegram_user(
        init_data
    )

    if not user:

        return jsonify(
            success=False,
            error=
                "Telegram не подтверждён"
        ), 401


    uid = int(
        user["id"]
    )


    # Проверяем подписку
    if not is_subscribed(uid):

        return jsonify(
            success=False,
            error=
                "Сначала подпишитесь"
        ), 403


    # Получаем ID пригласившего
    referrer_id =
        data.get(
            "referrer_id"
        )


    try:

        if referrer_id:

            referrer_id = int(
                referrer_id
            )

        else:

            referrer_id = None


    except (
        TypeError,
        ValueError
    ):

        referrer_id = None


    # Создаём пользователя
    # и засчитываем реферала
    row = upsert_user(
        user,
        referrer_id
    )


    # Реферальная ссылка
    # теперь сразу открывает Mini App

    ref_link = (
        "https://t.me/"
        f"{BOT_USERNAME}"
        "?startapp=ref_"
        f"{uid}"
    )


    return jsonify(

        success=True,

        telegram_id=
            row["telegram_id"],

        username=
            row["username"],

        first_name=
            row["first_name"],

        balance=
            row["balance"],

        referrals=
            row["referrals"],

        ref_link=
            ref_link

    )


# ============================================================
# CHECK SUBSCRIPTION
# ============================================================

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


    subscribed =
        is_subscribed(
            int(user["id"])
        )


    return jsonify(
        subscribed=subscribed
    )


# ============================================================
# LEADERS
# ============================================================

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

            name =
                "@" +
                row["username"]

        else:

            name =
                row["first_name"] or
                "Пользователь"


        leaders.append({

            "name":
                name,

            "referrals":
                row["referrals"]

        })


    return jsonify(

        success=True,

        leaders=leaders

    )


# ============================================================
# WITHDRAW
# ============================================================

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

            error=
                "Telegram не подтверждён"

        ), 401


    uid = int(
        user["id"]
    )


    if not is_subscribed(uid):

        return jsonify(

            success=False,

            error=
                "Сначала подпишитесь"

        ), 403


    try:

        amount = float(
            data.get(
                "amount"
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify(

            success=False,

            error=
                "Некорректная сумма"

        ), 400


    if amount <= 0:

        return jsonify(

            success=False,

            error=
                "Некорректная сумма"

        ), 400


    if (
        not BOT_TOKEN
        or not ADMIN_CHAT_ID
    ):

        return jsonify(

            success=False,

            error=
                "Настройки Telegram "
                "не установлены"

        ), 500


    conn = get_db()


    row = conn.execute(
        """
        SELECT balance
        FROM users
        WHERE telegram_id = ?
        """,
        (uid,)
    ).fetchone()


    if not row:

        conn.close()

        return jsonify(

            success=False,

            error=
                "Пользователь не найден"

        ), 404


    balance = float(
        row["balance"]
    )


    if amount > balance:

        conn.close()

        return jsonify(

            success=False,

            error=
                "Недостаточно Stars"

        ), 400


    username =
        user.get(
            "username"
        )


    first_name =
        user.get(
            "first_name",
            ""
        )


    display_name =
        username or
        first_name or
        "Не указан"


    text = (

        "💸 НОВАЯ ЗАЯВКА "
        "НА ВЫВОД\n\n"

        f"👤 Пользователь: "
        f"@{display_name}\n"

        f"🆔 Telegram ID: "
        f"{uid}\n"

        f"⭐ Сумма: "
        f"{amount:g} Stars\n"

        f"💰 Баланс: "
        f"{balance:g} Stars"

    )


    try:

        response =
            requests.post(

                "https://api.telegram.org/"
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


    except Exception as e:

        print(
            "Withdraw Telegram error:",
            e
        )

        conn.close()

        return jsonify(

            success=False,

            error=
                "Ошибка Telegram"

        ), 500


    if not result.get("ok"):

        conn.close()

        return jsonify(

            success=False,

            error=
                "Telegram не принял заявку"

        ), 500


    new_balance =
        balance - amount


    conn.execute(

        """
        UPDATE users
        SET balance = ?
        WHERE telegram_id = ?
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

        balance=
            new_balance

    )


# ============================================================
# TELEGRAM BOT WEBHOOK
# ============================================================

@app.route(
    "/telegram-webhook",
    methods=["POST"]
)
def telegram_webhook():

    update =
        request.get_json(
            silent=True
        ) or {}


    print(
        "Telegram update:",
        update
    )


    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    message =
        update.get(
            "message"
        )


    if message:

        chat =
            message.get(
                "chat",
                {}
            )

        chat_id =
            chat.get(
                "id"
            )


        text =
            message.get(
                "text",
                ""
            )


        if (
            chat_id
            and text.startswith(
                "/start"
            )
        ):

            # Кнопка Mini App
            keyboard = {

                "inline_keyboard": [[

                    {

                        "text":
                            "🎁 Открыть GiftsUpp",

                        "web_app": {

                            "url":
                                WEBAPP_URL

                        }

                    }

                ]]

            }


            send_url =
                (
                    "https://api.telegram.org/"
                    f"bot{BOT_TOKEN}/sendMessage"
                )


            try:

                requests.post(

                    send_url,

                    json={

                        "chat_id":
                            chat_id,

                        "text":
                            (
                                "🎁 Добро пожаловать "
                                "в GiftsUpp!\n\n"
                                "Открой приложение "
                                "кнопкой ниже."
                            ),

                        "reply_markup":
                            keyboard

                    },

                    timeout=10

                )

            except Exception as e:

                print(
                    "Bot send error:",
                    e
                )


    return jsonify(
        ok=True
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/health"
)
def health():

    return jsonify({

        "status":
            "ok",

        "app":
            "GiftsUpp",

        "bot":
            BOT_USERNAME,

        "webapp":
            WEBAPP_URL

    })


# ============================================================
# DATABASE INIT
# ============================================================

init_db()


# ============================================================
# START
# ============================================================

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
