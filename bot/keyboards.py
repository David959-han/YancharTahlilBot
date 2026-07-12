from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📊 Binance Top 99", callback_data="top_coins")],
        [
            InlineKeyboardButton("🟢 ↑ Oshganlar", callback_data="gainers_24h"),
            InlineKeyboardButton("🔴 ↓ Tushganlar", callback_data="losers_24h"),
        ],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)


def coin_detail_keyboard(coin_id: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🤖 AI Tahlil", callback_data=f"analyze_{coin_id}")],
        [InlineKeyboardButton("🔄 Yangilash", callback_data=f"refresh_{coin_id}")],
        [InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)


def top_coins_keyboard(coins: list[dict]) -> InlineKeyboardMarkup:
    """Top coinlar ro'yxati — har biri tugma."""
    keyboard = []
    row = []
    for i, coin in enumerate(coins):
        symbol = coin.get("symbol", "").upper()
        change = coin.get("price_change_percentage_24h", 0) or 0
        icon = "🟢" if change >= 0 else "🔴"
        btn = InlineKeyboardButton(
            f"{icon} {symbol}",
            callback_data=f"coin_{coin['id']}"
        )
        row.append(btn)
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)
