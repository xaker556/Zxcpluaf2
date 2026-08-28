@app.route(
    "/api/referral",
    methods=["POST"]
)
def api_referral():

    data = request.get_json(
        silent=True
    ) or {}

    secret = data.get("secret")

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
        user_id = int(data.get("user_id"))
        referrer_id = int(data.get("referrer_id"))
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
        return jsonify(
            success=False,
            error="Реферер не найден"
        ), 404

    user = conn.execute(
        """
        SELECT telegram_id, referred_by
        FROM users
        WHERE telegram_id=?
        """,
        (user_id,)
    ).fetchone()

    if user and user["referred_by"] is not None:
        conn.close()
        return jsonify(
            success=True,
            counted=False,
            reward=0,
            message="Реферал уже был засчитан"
        )

    if user is None:
        conn.execute(
            """
            INSERT INTO users (
                telegram_id,
                referred_by
            )
            VALUES (?, ?)
            """,
            (user_id, referrer_id)
        )
    else:
        conn.execute(
            """
            UPDATE users
            SET referred_by=?
            WHERE telegram_id=?
            """,
            (referrer_id, user_id)
        )

    # Начисляем пригласившему 0.85 Stars
    conn.execute(
        """
        UPDATE users
        SET referrals = referrals + 1,
            balance = balance + 0.85
        WHERE telegram_id=?
        """,
        (referrer_id,)
    )

    conn.commit()

    row = conn.execute(
        """
        SELECT balance
        FROM users
        WHERE telegram_id=?
        """,
        (referrer_id,)
    ).fetchone()

    new_balance = row["balance"]

    conn.close()

    return jsonify(
        success=True,
        counted=True,
        reward=0.85,
        balance=new_balance
    )
