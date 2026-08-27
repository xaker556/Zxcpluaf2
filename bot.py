import os
import logging
import sqlite3

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import BadRequest, Forbidden, TelegramError


BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL = "@eclipsedlf"
CHANNEL_URL = "https://t.me/eclipsedlf"

WITHDRAW_ADMIN = "@Eclipsed_consult"

REFERRAL_REWARD = 0.50
MIN_WITHDRAW = 15

PROMO = "44621"
PROMO_REWARD = 10.0
PROMO_LIMIT = 10


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


db = sqlite3.connect(
    "bot.db",
    check_same_thread=False
)

cursor = db.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance REAL DEFAULT 0,
    invited_by INTEGER,
    referrals INTEGER DEFAULT 0,
    subscribed INTEGER DEFAULT 0
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS promo_uses (
    user_id INTEGER PRIMARY KEY,
    promo TEXT NOT NULL
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS promos (
    promo TEXT PRIMARY KEY,
    reward REAL,
    max_uses INTEGER,
    uses INTEGER DEFAULT 0
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    amount REAL,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")


cursor.execute(
    """
    INSERT OR IGNORE INTO promos
    (promo, reward, max_uses, uses)
    VALUES (?, ?, ?, 0)
    """,
    (PROMO, PROMO_REWARD, PROMO_LIMIT)
)

db.commit()


def keyboard():
    return ReplyKeyboardMarkup(
        [
            ["💰 Баланс", "👥 Рефералы"],
            ["💸 Вывод", "🎁 Промокод"],
            ["📢 Канал"]
        ],
        resize_keyboard=True
    )


def get_user(user_id: int, username: str = ""):

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user_id,)
    )

    exists = cursor.fetchone()

    if not exists:
        cursor.execute(
            """
            INSERT INTO users
            (user_id, username)
            VALUES (?, ?)
            """,
            (user_id, username)
        )
    else:
        cursor.execute(
            """
            UPDATE users
            SET username = ?
            WHERE user_id = ?
            """,
            (username, user_id)
        )

    db.commit()


async def is_subscribed(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int
) -> bool:

    try:
        member = await context.bot.get_chat_member(
            CHANNEL,
            user_id
        )

        return member.status in (
            "member",
            "administrator",
            "creator"
        )

    except (BadRequest, Forbidden):
        return False

    except TelegramError as e:
        logger.warning(
            f"Ошибка проверки подписки: {e}"
        )
        return False


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    get_user(
        user.id,
        user.username or ""
    )

    # Реферальная ссылка
    if context.args:

        try:
            inviter_id = int(context.args[0])

            if inviter_id != user.id:

                cursor.execute(
                    """
                    SELECT user_id
                    FROM users
                    WHERE user_id = ?
                    """,
                    (inviter_id,)
                )

                if cursor.fetchone():

                    cursor.execute(
                        """
                        SELECT invited_by
                        FROM users
                        WHERE user_id = ?
                        """,
                        (user.id,)
                    )

                    row = cursor.fetchone()

                    if row and row[0] is None:

                        cursor.execute(
                            """
                            UPDATE users
                            SET invited_by = ?
                            WHERE user_id = ?
                            """,
                            (inviter_id, user.id)
                        )

                        db.commit()

        except (ValueError, TypeError):
            pass


    # Проверка подписки
    if not await is_subscribed(
        context,
        user.id
    ):

        await update.message.reply_text(
            "👋 Привет!\n\n"
            "Чтобы пользоваться ботом, "
            "подпишись на канал @eclipsedlf.\n\n"
            "После подписки снова нажми /start.",
            reply_markup=keyboard()
        )

        return


    cursor.execute(
        """
        SELECT invited_by, subscribed
        FROM users
        WHERE user_id = ?
        """,
        (user.id,)
    )

    data = cursor.fetchone()

    if data:

        inviter_id = data[0]
        was_subscribed = data[1]

        if was_subscribed == 0:

            if inviter_id:

                cursor.execute(
                    """
                    UPDATE users
                    SET balance = balance + ?,
                        referrals = referrals + 1
                    WHERE user_id = ?
                    """,
                    (
                        REFERRAL_REWARD,
                        inviter_id
                    )
                )

            cursor.execute(
                """
                UPDATE users
                SET subscribed = 1
                WHERE user_id = ?
                """,
                (user.id,)
            )

            db.commit()


    await update.message.reply_text(
        "✅ Подписка подтверждена!\n\n"
        f"⭐ Приглашай пользователей и получай "
        f"{REFERRAL_REWARD} Stars за каждого.",
        reply_markup=keyboard()
    )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    text = update.message.text.strip()

    get_user(
        user.id,
        user.username or ""
    )


    # Проверка подписки
    if not await is_subscribed(
        context,
        user.id
    ):

        await update.message.reply_text(
            "❌ Сначала подпишись на @eclipsedlf.",
            reply_markup=keyboard()
        )

        return


    # ================= ВВОД СУММЫ ВЫВОДА =================

    if context.user_data.get("waiting_withdraw"):

        try:
            amount = int(text)

        except ValueError:

            await update.message.reply_text(
                "❌ Введи целое число Stars.\n\n"
                "Например: 15",
                reply_markup=keyboard()
            )

            return


        if amount < MIN_WITHDRAW:

            await update.message.reply_text(
                f"❌ Минимальный вывод — "
                f"{MIN_WITHDRAW} ⭐.",
                reply_markup=keyboard()
            )

            return


        cursor.execute(
            """
            SELECT balance
            FROM users
            WHERE user_id = ?
            """,
            (user.id,)
        )

        data = cursor.fetchone()

        balance = data[0] if data else 0


        if amount > balance:

            await update.message.reply_text(
                f"❌ Недостаточно Stars.\n\n"
                f"💰 Баланс: {balance:.2f} ⭐\n"
                f"💸 Запрошено: {amount} ⭐",
                reply_markup=keyboard()
            )

            return


        try:

            cursor.execute("BEGIN IMMEDIATE")

            cursor.execute(
                """
                SELECT balance
                FROM users
                WHERE user_id = ?
                """,
                (user.id,)
            )

            current = cursor.fetchone()

            if not current or current[0] < amount:

                db.rollback()

                await update.message.reply_text(
                    "❌ Недостаточно Stars.",
                    reply_markup=keyboard()
                )

                return


            cursor.execute(
                """
                UPDATE users
                SET balance = balance - ?
                WHERE user_id = ?
                """,
                (
                    amount,
                    user.id
                )
            )


            cursor.execute(
                """
                INSERT INTO withdrawals
                (user_id, username, amount, status)
                VALUES (?, ?, ?, 'pending')
                """,
                (
                    user.id,
                    user.username or "",
                    amount
                )
            )

            withdrawal_id = cursor.lastrowid

            db.commit()


            username_text = (
                f"@{user.username}"
                if user.username
                else "нет username"
            )


            admin_message = (
                "💸 НОВАЯ ЗАЯВКА НА ВЫВОД\n\n"
                f"⭐ Сумма: {amount} Stars\n"
                f"👤 Пользователь: {username_text}\n"
                f"🆔 ID: {user.id}\n"
                f"📋 Заявка №{withdrawal_id}\n\n"
                "⏳ Статус: ожидает обработки"
            )


            try:

                await context.bot.send_message(
                    chat_id=WITHDRAW_ADMIN,
                    text=admin_message
                )

            except TelegramError as e:

                logger.error(
                    f"Не удалось отправить заявку админу: {e}"
                )

                cursor.execute(
                    """
                    UPDATE users
                    SET balance = balance + ?
                    WHERE user_id = ?
                    """,
                    (
                        amount,
                        user.id
                    )
                )

                cursor.execute(
                    """
                    UPDATE withdrawals
                    SET status = 'failed'
                    WHERE id = ?
                    """,
                    (withdrawal_id,)
                )

                db.commit()

                await update.message.reply_text(
                    "❌ Не удалось отправить заявку.\n\n"
                    "⭐ Stars возвращены на баланс.",
                    reply_markup=keyboard()
                )

                context.user_data["waiting_withdraw"] = False

                return


            context.user_data["waiting_withdraw"] = False


            await update.message.reply_text(
                "✅ Заявка на вывод отправлена!\n\n"
                f"⭐ Сумма: {amount} Stars\n"
                f"📋 Заявка №{withdrawal_id}\n\n"
                "⏳ Ожидай обработки.",
                reply_markup=keyboard()
            )

        except Exception as e:

            db.rollback()

            logger.error(
                f"Ошибка вывода: {e}"
            )

            await update.message.reply_text(
                "❌ Произошла ошибка. "
                "Попробуй позже.",
                reply_markup=keyboard()
            )

        return


    # ================= БАЛАНС =================

    if text == "💰 Баланс":

        cursor.execute(
            """
            SELECT balance, referrals
            FROM users
            WHERE user_id = ?
            """,
            (user.id,)
        )

        data = cursor.fetchone()

        balance = data[0] if data else 0
        referrals = data[1] if data else 0

        await update.message.reply_text(
            f"💰 Баланс: {balance:.2f} ⭐\n"
            f"👥 Рефералов: {referrals}",
            reply_markup=keyboard()
        )

        return


    # ================= РЕФЕРАЛЫ =================

    if text == "👥 Рефералы":

        bot = await context.bot.get_me()

        referral_link = (
            f"https://t.me/{bot.username}"
            f"?start={user.id}"
        )

        await update.message.reply_text(
            "👥 Твоя реферальная ссылка:\n\n"
            f"{referral_link}\n\n"
            f"⭐ За одного приглашённого: "
            f"{REFERRAL_REWARD} Stars",
            reply_markup=keyboard()
        )

        return


    # ================= ПРОМОКОД =================

    if text == "🎁 Промокод":

        await update.message.reply_text(
            "🎁 Введите промокод:",
            reply_markup=keyboard()
        )

        return


    if text == PROMO:

        try:

            cursor.execute("BEGIN IMMEDIATE")

            cursor.execute(
                """
                SELECT user_id
                FROM promo_uses
                WHERE user_id = ?
                """,
                (user.id,)
            )

            if cursor.fetchone():

                db.rollback()

                await update.message.reply_text(
                    "❌ Вы уже использовали "
                    "этот промокод.",
                    reply_markup=keyboard()
                )

                return


            cursor.execute(
                """
                SELECT reward, max_uses, uses
                FROM promos
                WHERE promo = ?
                """,
                (PROMO,)
            )

            promo_data = cursor.fetchone()

            if not promo_data:

                db.rollback()

                await update.message.reply_text(
                    "❌ Промокод недоступен.",
                    reply_markup=keyboard()
                )

                return


            reward, max_uses, uses = promo_data


            if uses >= max_uses:

                db.rollback()

                await update.message.reply_text(
                    "❌ Все активации промокода "
                    "закончились.",
                    reply_markup=keyboard()
                )

                return


            cursor.execute(
                """
                UPDATE users
                SET balance = balance + ?
                WHERE user_id = ?
                """,
                (
                    reward,
                    user.id
                )
            )


            cursor.execute(
                """
                INSERT INTO promo_uses
                (user_id, promo)
                VALUES (?, ?)
                """,
                (
                    user.id,
                    PROMO
                )
            )


            cursor.execute(
                """
                UPDATE promos
                SET uses = uses + 1
                WHERE promo = ?
                """,
                (PROMO,)
            )

            db.commit()


            await update.message.reply_text(
                "🎉 Промокод активирован!\n\n"
                f"⭐ Получено: {reward} Stars",
                reply_markup=keyboard()
            )

        except Exception as e:

            db.rollback()

            logger.error(
                f"Ошибка промокода: {e}"
            )

            await update.message.reply_text(
                "❌ Произошла ошибка. "
                "Попробуйте позже.",
                reply_markup=keyboard()
            )

        return


    # ================= ВЫВОД =================

    if text == "💸 Вывод":

        cursor.execute(
            """
            SELECT balance
            FROM users
            WHERE user_id = ?
            """,
            (user.id,)
        )

        data = cursor.fetchone()

        balance = data[0] if data else 0


        if balance < MIN_WITHDRAW:

            await update.message.reply_text(
                f"💸 Минимальный вывод: "
                f"{MIN_WITHDRAW} ⭐\n\n"
                f"💰 Твой баланс: "
                f"{balance:.2f} ⭐",
                reply_markup=keyboard()
            )

            return


        context.user_data["waiting_withdraw"] = True


        await update.message.reply_text(
            "💸 Вывод Stars\n\n"
            f"💰 Твой баланс: {balance:.2f} ⭐\n"
            f"📉 Минимальный вывод: {MIN_WITHDRAW} ⭐\n\n"
            "✏️ Напиши количество Stars, "
            "которое хочешь вывести.\n\n"
            "Например: 15",
            reply_markup=keyboard()
        )

        return


    # ================= КАНАЛ =================

    if text == "📢 Канал":

        await update.message.reply_text(
            f"📢 Наш Telegram-канал:\n"
            f"{CHANNEL_URL}",
            reply_markup=keyboard()
        )

        return


# ================= ЗАПУСК =================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN не найден в переменных "
            "окружения / GitHub Secrets"
        )


    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )


    app.add_handler(
        CommandHandler("start", start)
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )


    logger.info("Bot started!")

    app.run_polling()


if __name__ == "__main__":
    main()


