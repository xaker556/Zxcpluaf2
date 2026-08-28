import os
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/withdraw", methods=["POST"])
def withdraw():

    data = request.get_json(silent=True) or {}

    amount = data.get("amount")
    username = data.get("username", "Не указан")

    if not amount:
        return jsonify({
            "success": False,
            "error": "Не указана сумма"
        }), 400

    if not BOT_TOKEN:
        return jsonify({
            "success": False,
            "error": "BOT_TOKEN не настроен"
        }), 500

    if not ADMIN_CHAT_ID:
        return jsonify({
            "success": False,
            "error": "ADMIN_CHAT_ID не настроен"
        }), 500

    text = (
        "💸 НОВАЯ ЗАЯВКА НА ВЫВОД\n\n"
        f"👤 Пользователь: {username}\n"
        f"⭐ Сумма: {amount} Stars\n\n"
        "📌 Статус: Новая заявка"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": ADMIN_CHAT_ID,
                "text": text
            },
            timeout=15
        )

        result = response.json()

    except Exception:
        return jsonify({
            "success": False,
            "error": "Ошибка соединения с Telegram"
        }), 500

    if not result.get("ok"):
        return jsonify({
            "success": False,
            "error": "Telegram не принял сообщение"
        }), 500

    return jsonify({
        "success": True
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
)
