import os
import time
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv(
"WEBAPP_URL",
"https://zxcpluaf2.onrender.com"
)

API_URL = WEBAPP_URL.rstrip("/")

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

def open_app_keyboard():
return {
"inline_keyboard": [
[
{
"text": "🎁 Открыть GiftsUpp",
"web_app": {
"url": API_URL
}
}
]
]
}

def save_referral(user_id, referrer_id):
if not referrer_id:
return False

try:  
    referrer_id = int(referrer_id)  
    user_id = int(user_id)  
except Exception:  
    return False  

if referrer_id == user_id:  
    return False  

try:  
    response = requests.post(  
        f"{API_URL}/api/referral",  
        json={  
            "user_id": user_id,  
            "referrer_id": referrer_id,  
            "secret": BOT_TOKEN  
        },  
        timeout=15  
    )  

    result = response.json()  

    print(  
        "Referral:",  
        user_id,  
        "from",  
        referrer_id,  
        result  
    )  

    return result.get("success", False)  

except Exception as e:  
    print("Referral API error:", e)  
    return False

def handle_start(message):
chat = message.get("chat", {})
user = message.get("from", {})

chat_id = chat.get("id")  
user_id = user.get("id")  

if not chat_id or not user_id:  
    return  

text = message.get("text", "")  
parts = text.split(maxsplit=1)  

referrer_id = None  

if len(parts) > 1:  
    argument = parts[1].strip()  

    if argument.startswith("ref_"):  
        try:  
            referrer_id = int(  
                argument.replace("ref_", "", 1)  
            )  
        except Exception:  
            referrer_id = None  

if referrer_id:  
    save_referral(  
        user_id,  
        referrer_id  
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

def process_update(update):
message = update.get("message")

if not message:  
    return  

text = message.get("text", "")  

if text.startswith("/start"):  
    handle_start(message)

def main():
print("GiftsUpp bot started")

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

        offset = update["update_id"] + 1  

        try:  
            process_update(update)  

        except Exception as e:  
            print(  
                "Update error:",  
                e  
            )  

    time.sleep(0.2)

if name == "main":
main()
