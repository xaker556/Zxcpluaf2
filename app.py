import os
import sqlite3

from flask import Flask, request, jsonify


app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_FILE = "giftsupp.db"


def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            referred_by INTEGER,
            referrals INTEGER NOT NULL DEFAULT 0,
            balance REAL NOT NULL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return "GiftsUpp работает!"


@app.route("/api/referral", methods=["POST"])
def api_referral():

    data = request.get_json(silent=True) or {}

    secret = data.get("secret")
    user_id = data.get("user_id")
    referrer_id = data.get("referrer_id")

    if not BOT_TOKEN:
        return jsonify(
            success=False,
            error="BOT_TOKEN не установлен"
        ), 500

    if secret != BOT_TOKEN:
        return jsonify(
            success=False,
            error="Доступ запрещён"
        ), 403

    try:
        user_id = int(user_id)
        referrer_id = int(referrer_id)
    except (TypeError, ValueError):
        return jsonify(
            success=False,
            error="Некорректный ID"
        ), 400

    if user_id == referrer_id:
        return jsonify(
            success=False,
            error="Нельзя пригласить самого себя"
        ), 400

    conn = get_db()

    try:

        # Создаём пригласившего, если его ещё нет
        conn.execute("""
            INSERT OR IGNORE INTO users (
                telegram_id,
                referred_by,
                referrals,
                balance
            )
            VALUES (?, NULL, 0, 0)
        """, (referrer_id,))

        # Проверяем пользователя
        user = conn.execute("""
            SELECT telegram_id, referred_by
            FROM users
            WHERE telegram_id = ?
        """, (user_id,)).fetchone()

        # Уже был приглашён
        if user and user["referred_by"] is not None:
            conn.close()

            return jsonify(
                success=True,
                counted=False,
                reward=0,
                message="Реферал уже был засчитан"
            )

        # Новый пользователь
        if user is None:

            conn.execute("""
                INSERT INTO users (
                    telegram_id,
                    referred_by,
                    referrals,
                    balance
                )
                VALUES (?, ?, 0, 0)
            """, (
                user_id,
                referrer_id
            ))

        else:

            conn.execute("""
                UPDATE users
                SET referred_by = ?
                WHERE telegram_id = ?
            """, (
                referrer_id,
                user_id
            ))

        # Начисляем 0.85 Stars
        conn.execute("""
            UPDATE users
            SET
                referrals = referrals + 1,
                balance = balance + 0.85
            WHERE telegram_id = ?
        """, (referrer_id,))

        conn.commit()

        row = conn.execute("""
            SELECT balance
            FROM users
            WHERE telegram_id = ?
        """, (referrer_id,)).fetchone()

        new_balance = row["balance"]

        conn.close()

        print(
            f"⭐ Реферал: {referrer_id} "
            f"+0.85 Stars за {user_id}"
        )

        return jsonify(
            success=True,
            counted=True,
            reward=0.85,
            balance=new_balance
        )

    except Exception as e:

        conn.rollback()
        conn.close()

        print(
            "Referral error:",
            e
        )

        return jsonify(
            success=False,
            error="Ошибка базы данных"
        ), 500


init_db()


if __name__ == "__main__":

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
