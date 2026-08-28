<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GiftsUpp</title>

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

.check {
    background: #21172b;
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

.ref-link {
    word-break: break-all;
    margin-top: 10px;
    padding: 13px;
    border-radius: 10px;
    background: #100b16;
    color: #b8a9c0;
    font-size: 12px;
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

.refs {
    color: #9d91a5;
}

.history {
    margin-bottom: 9px;
    padding: 14px;
    background: #19121f;
    border-radius: 13px;
    border: 1px solid #30223a;
    display: flex;
    justify-content: space-between;
}

.history small {
    color: #8d8295;
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
</style>
</head>

<body>

<div class="app">

<!-- ГЛАВНАЯ -->
<div id="home" class="page active">

<header>
    <div class="logo">🎁 GiftsUpp</div>
    <div class="subtitle">Подарки • Stars • Рефералы</div>
</header>

<div class="balance">
    <div class="balance-title">Ваш баланс</div>
    <div class="balance-value" id="balance">
        ⭐ 1 250
    </div>
</div>

<div class="user-box">
    <div class="avatar">🎁</div>

    <div>
        <div class="user-name" id="username">
            Test User
        </div>

        <div class="user-status">
            Пользователь
        </div>
    </div>
</div>

<div class="section">

<div class="section-title">Аккаунт</div>

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

<div class="section-title">Telegram</div>

<button class="full check"
onclick="showPage('subscription')">

📢 Проверить подписку

</button>

</div>

</div>


<!-- ВЫВОД -->
<div id="withdraw" class="page">

<header>
    <div class="logo">💸 Вывод</div>
    <div class="subtitle">Создание заявки</div>
</header>

<button class="back" onclick="showPage('home')">
    ← Назад
</button>

<div class="card">

<div class="card-title">
    Доступно
</div>

<div class="balance-value">
    ⭐ 1 250
</div>

</div>

<div class="card">

<div class="card-title">
    Сумма вывода
</div>

<div class="card-text">
    Укажите количество Stars.
    <br><br>
    Коэффициент GiftsUpp: <b>0.85 ⭐</b>
</div>

<input
    type="number"
    id="withdrawAmount"
    placeholder="Например: 500"
    min="1">

<button
    class="action"
    onclick="createWithdraw()">

    💸 Рассчитать

</button>

</div>

<div id="withdrawMessage" class="notice">
    Заявка будет рассчитана в тестовом режиме.
</div>

</div>


<!-- РЕФЕРАЛЫ -->
<div id="referrals" class="page">

<header>
    <div class="logo">👥 Рефералы</div>
    <div class="subtitle">Приглашай пользователей</div>
</header>

<button class="back" onclick="showPage('home')">
    ← Назад
</button>

<div class="card">

<div class="card-title">
    Приглашено
</div>

<div class="balance-value">
    0
</div>

</div>

<div class="card">

<div class="card-title">
    Твоя ссылка
</div>

<div class="ref-link" id="refLink">
https://t.me/GiftsUpp_bot?start=ref_TEST
</div>

<button class="action"
onclick="copyReferral()">

📋 Скопировать

</button>

</div>

</div>


<!-- ПРОМОКОД -->
<div id="promo" class="page">

<header>
    <div class="logo">🎟 Промокод</div>
    <div class="subtitle">Активация промокода</div>
</header>

<button class="back" onclick="showPage('home')">
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

<button class="action"
onclick="activatePromo()">

🎟 Активировать

</button>

</div>

<div id="promoMessage" class="notice">
    Введите промокод.
</div>

</div>


<!-- ИСТОРИЯ -->
<div id="history" class="page">

<header>
    <div class="logo">📜 История</div>
    <div class="subtitle">Операции</div>
</header>

<button class="back" onclick="showPage('home')">
    ← Назад
</button>

<div class="section">

<div class="history">
    <span>
        🎁 Бонус<br>
        <small>Сегодня</small>
    </span>
    <span>+100 ⭐</span>
</div>

<div class="history">
    <span>
        👥 Реферальный бонус<br>
        <small>Вчера</small>
    </span>
    <span>+50 ⭐</span>
</div>

</div>

</div>


<!-- ПОДПИСКА -->
<div id="subscription" class="page">

<header>
    <div class="logo">📢 Подписка</div>
    <div class="subtitle">Проверка подписки</div>
</header>

<button class="back" onclick="showPage('home')">
    ← Назад
</button>

<div class="card">

<div class="card-title">
    @eclipsedlf
</div>

<div class="card-text">
    Подпишись на канал и проверь подписку.
</div>

<button class="action"
onclick="openChannel()">

📢 Открыть канал

</button>

<button class="action"
onclick="checkSubscription()">

✅ Проверить подписку

</button>

</div>

<div id="subscriptionMessage" class="notice">
    Статус пока не проверен.
</div>

</div>


<!-- ЛИДЕРБОРД -->
<div id="leaders" class="page">

<header>
    <div class="logo">🏆 Лидерборд</div>
    <div class="subtitle">
        Топ по приглашениям
    </div>
</header>

<div class="leader">
    <span>🥇 @username1</span>
    <span class="refs">128</span>
</div>

<div class="leader">
    <span>🥈 @username2</span>
    <span class="refs">96</span>
</div>

<div class="leader">
    <span>🥉 @username3</span>
    <span class="refs">74</span>
</div>

<div class="leader">
    <span>4. @username4</span>
    <span class="refs">61</span>
</div>

<div class="leader">
    <span>5. @username5</span>
    <span class="refs">48</span>
</div>

<div class="leader">
    <span>6. @username6</span>
    <span class="refs">37</span>
</div>

<div class="leader">
    <span>7. @username7</span>
    <span class="refs">29</span>
</div>

<div class="leader">
    <span>8. @username8</span>
    <span class="refs">21</span>
</div>

<div class="leader">
    <span>9. @username9</span>
    <span class="refs">16</span>
</div>

<div class="leader">
    <span>10. @username10</span>
    <span class="refs">12</span>
</div>

</div>

</div>


<!-- НИЖНЕЕ МЕНЮ -->
<div class="bottom">

<button id="homeBtn"
class="active"
onclick="showPage('home')">

🏠<br>Главная

</button>

<button id="leadersBtn"
onclick="showPage('leaders')">

🏆<br>Лидеры

</button>

<button id="supportBtn"
onclick="openSupport()">

🛠<br>Поддержка

</button>

</div>


<script>

/* НАВИГАЦИЯ */

function showPage(page) {

    document.querySelectorAll('.page')
        .forEach(p => p.classList.remove('active'));

    document.getElementById(page)
        .classList.add('active');

    document.getElementById('homeBtn')
        .classList.remove('active');

    document.getElementById('leadersBtn')
        .classList.remove('active');

    if (page === 'home') {
        document.getElementById('homeBtn')
            .classList.add('active');
    }

    if (page === 'leaders') {
        document.getElementById('leadersBtn')
            .classList.add('active');
    }

    window.scrollTo(0, 0);
}


/* ВЫВОД — ТЕСТ 0.85 */

function createWithdraw() {

    const amount =
        Number(document.getElementById('withdrawAmount').value);

    const message =
        document.getElementById('withdrawMessage');

    if (!amount || amount <= 0) {

        message.innerText =
            '❌ Укажите корректную сумму.';

        return;
    }

    const result = amount * 0.85;

    message.innerHTML =
        '✅ Тестовая заявка рассчитана!<br><br>' +
        'Введено: ⭐ ' + amount.toFixed(2) +
        '<br>' +
        'К выдаче: ⭐ ' + result.toFixed(2) +
        '<br><br>' +
        '⚙️ Коэффициент: 0.85';
}


/* РЕФЕРАЛЫ */

function copyReferral() {

    navigator.clipboard.writeText(
        document.getElementById('refLink').innerText
    );

    alert('✅ Ссылка скопирована!');
}


/* ПРОМОКОД */

function activatePromo() {

    const code =
        document.getElementById('promoCode').value.trim();

    const message =
        document.getElementById('promoMessage');

    if (!code) {

        message.innerText =
            '❌ Введите промокод.';

        return;
    }

    if (code.toUpperCase() === 'GIFTS100') {

        message.innerText =
            '✅ Тестовый промокод принят! +100 ⭐';

    } else {

        message.innerText =
            '❌ Промокод не найден.';
    }
}


/* КАНАЛ */

function openChannel() {

    window.open(
        'https://t.me/eclipsedlf',
        '_blank'
    );
}


/* ПОДПИСКА */

function checkSubscription() {

    const message =
        document.getElementById('subscriptionMessage');

    message.innerText =
        '🔄 Проверяем подписку...';

    setTimeout(() => {

        message.innerText =
            '⚠️ Это тестовая проверка. Реальная проверка будет подключена через Telegram Bot API.';

    }, 1000);
}


/* ПОДДЕРЖКА */

function openSupport() {

    const text = encodeURIComponent(
        'Здравствуйте! Хочу сообщить о проблеме в GiftsUpp.'
    );

    window.open(
        'https://t.me/Eclipsed_consult?text=' + text,
        '_blank'
    );
}

</script>

</body>
</html>
