import os
import sqlite3
import json
import hmac
import hashlib
import urllib.parse
import requests
import threading
import time

from flask import Flask, request, jsonify, Response


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
# TELEGRAM WEB APP AUTH
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
            f"https://api
