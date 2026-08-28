@app.route("/api/referral", methods=["POST"])
def api_referral():
    data = request.get_json(silent=True) or {}

    # Проверяем секрет
    if data.get("secret") != BOT_TOKEN:
        return jsonify(
            success=False,
            error="Недействительный секрет"
        ), 403

    try:
        user_id = int(data.get("user_id"))
        referrer_id = int(data.get("referrer_id"))
    except (TypeError, ValueError):
        return jsonify(
            success=False,
            error="Некорректные ID"
        ), 400

    # Нельзя пригласить самого себя
    if user_id == referrer_id:
        return jsonify(
            success=False,
            error="Нельзя пригласить себя"
        ), 400

    conn = get_db()

    # Проверяем пригласившего
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
            error="Пригласивший не найден"
        ), 404

    # Проверяем, существует ли новый пользователь
    user = conn.execute(
        """
        SELECT telegram_id, referred_by
        FROM users
        WHERE telegram_id=?
        """,
        (user_id,)
    ).fetchone()

    if user is None:

        conn.execute(
            """
            INSERT INTO users (
                telegram_id,
                referred_by
            )
            VALUES (?, ?)
            """,
            (
                user_id,
                referrer_id
            )
        )

        conn.execute(
            """
            UPDATE users
            SET referrals = referrals + 1
            WHERE telegram_id=?
            """,
            (referrer_id,)
        )

        conn.commit()
        conn.close()

        return jsonify(
            success=True,
            counted=True
        )

    # Если пользователь уже был кем-то приглашён,
    # повторно реферал не засчитываем
    if user["referred_by"] is not None:

        conn.close()

        return jsonify(
            success=True,
            counted=False,
            message="Реферал уже был засчитан"
        )

    # Записываем пригласившего
    conn.execute(
        """
        UPDATE users
        SET referred_by=?
        WHERE telegram_id=?
        """,
        (
            referrer_id,
            user_id
        )
    )

    # Увеличиваем количество рефералов
    conn.execute(
        """
        UPDATE users
        SET referrals = referrals + 1
        WHERE telegram_id=?
        """,
        (referrer_id,)
    )

    conn.commit()
    conn.close()

    return jsonify(
        success=True,
        counted=True
    )
