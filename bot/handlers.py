from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from services.coingecko import (
    get_coin_by_id, search_coin,
    format_price, format_market_cap, format_change,
)
from services.binance import get_top_binance_coins
from services.ai_analyzer import analyze_coin
from bot.keyboards import (
    main_menu_keyboard, coin_detail_keyboard,
    back_to_menu_keyboard, top_coins_keyboard,
)


WELCOME_TEXT = """🚀 <b>Yanchar Tahlil Botga Xush Kelibsiz!</b>

━━━━━━━━━━━━━━━━━━━━━
📈 <b>Kripto bozorini real vaqtda kuzating</b>
━━━━━━━━━━━━━━━━━━━━━

🔹 <b>Binance Top 99</b> — eng faol spot coinlar
🔹 <b>Istalgan coin</b> — shunchaki nomini yozing
🔹 <b>AI tahlil</b> — trader ko'zi bilan signal

💬 <b>Qanday ishlatish:</b>
Coin nomini yozing → <code>bitcoin</code> <code>eth</code> <code>sol</code> <code>pepe</code>

👇 <b>Boshlash uchun tugmani tanlang</b>"""

HELP_TEXT = """ℹ️ <b>Yordam</b>

<b>Komandalar:</b>
/start — Bosh menyu
/top — Binance top 99 coin
/coin &lt;nom&gt; — Coin qidirish

<b>Istalgan coinni qidirish mumkin:</b>
/coin bitcoin
/coin pepe
/coin sol

Yoki shunchaki coin nomini yozing — bot o'zi topadi!"""


def _build_coin_card(coin: dict) -> str:
    price = format_price(coin.get("current_price", 0))
    cap = format_market_cap(coin.get("market_cap", 0))
    volume = format_market_cap(coin.get("total_volume", 0))
    change_1h = format_change(coin.get("price_change_percentage_1h_in_currency") or coin.get("price_change_percentage_1h"))
    change_24h = format_change(coin.get("price_change_percentage_24h_in_currency") or coin.get("price_change_percentage_24h"))
    change_7d = format_change(coin.get("price_change_percentage_7d_in_currency") or coin.get("price_change_percentage_7d"))
    high = format_price(coin.get("high_24h", 0))
    low = format_price(coin.get("low_24h", 0))
    name = coin.get("name", "")
    symbol = coin.get("symbol", "").upper()

    return (
        f"📊 <b>{name} ({symbol})</b>\n\n"
        f"💰 <b>Narx:</b> {price}\n"
        f"⏱ <b>1 soat:</b> {change_1h}\n"
        f"🕛 <b>24 soat:</b> {change_24h}\n"
        f"📅 <b>7 kun:</b> {change_7d}\n\n"
        f"🔺 <b>24s yuqori:</b> {high}\n"
        f"🔻 <b>24s past:</b> {low}\n"
        f"🏦 <b>Market Cap:</b> {cap}\n"
        f"📦 <b>Hajm (24s):</b> {volume}\n"
    )


def _coin_data_for_ai(coin: dict) -> dict:
    return {
        "name": coin.get("name", ""),
        "symbol": coin.get("symbol", "").upper(),
        "current_price_fmt": format_price(coin.get("current_price", 0)),
        "change_1h": format_change(coin.get("price_change_percentage_1h_in_currency") or coin.get("price_change_percentage_1h")),
        "change_24h": format_change(coin.get("price_change_percentage_24h_in_currency") or coin.get("price_change_percentage_24h")),
        "change_7d": format_change(coin.get("price_change_percentage_7d_in_currency") or coin.get("price_change_percentage_7d")),
        "high_24h_fmt": format_price(coin.get("high_24h", 0)),
        "low_24h_fmt": format_price(coin.get("low_24h", 0)),
        "market_cap_fmt": format_market_cap(coin.get("market_cap", 0)),
        "volume_fmt": format_market_cap(coin.get("total_volume", 0)),
        "ath_change": f"{coin.get('ath_change_percentage', 0):.1f}%" if coin.get("ath_change_percentage") else "N/A",
    }


def _is_clean(coin: dict) -> bool:
    sym = coin.get("symbol", "")
    return sym.isascii() and sym.isalpha()


def _gainers(coins: list, n: int = 5) -> list:
    clean = [c for c in coins if _is_clean(c)]
    return sorted(clean, key=lambda c: c.get("price_change_percentage_24h") or 0, reverse=True)[:n]


def _losers(coins: list, n: int = 5) -> list:
    clean = [c for c in coins if _is_clean(c)]
    return sorted(clean, key=lambda c: c.get("price_change_percentage_24h") or 0)[:n]


def _build_overview(coins: list) -> str:
    """1-xabar: Gainers + Losers"""
    gainers = _gainers(coins, 5)
    losers = _losers(coins, 5)

    lines = [f"⚡️ <b>BINANCE TOP {len(coins)} — BOZOR OVERVIEW</b>\n"]
    lines.append("🚀 <b>TOP GAINERS — 24 soat</b>")
    for c in gainers:
        sym = c.get("symbol", "").upper()
        pct = c.get("price_change_percentage_24h", 0) or 0
        price = format_price(c.get("current_price", 0))
        lines.append(f"  🟢 <b>{sym}</b>  <code>+{pct:.2f}%</code>  {price}")

    lines.append("")
    lines.append("💀 <b>TOP LOSERS — 24 soat</b>")
    for c in losers:
        sym = c.get("symbol", "").upper()
        pct = c.get("price_change_percentage_24h", 0) or 0
        price = format_price(c.get("current_price", 0))
        lines.append(f"  🔴 <b>{sym}</b>  <code>{pct:.2f}%</code>  {price}")

    return "\n".join(lines)


def _build_full_list(coins: list) -> str:
    """2-xabar: 99 coin text ro'yxati"""
    lines = [f"💎 <b>BINANCE TOP {len(coins)} FAOL COIN</b> (24s hajm bo'yicha)\n"]
    for i, c in enumerate(coins, 1):
        sym = c.get("symbol", "").upper()
        price = format_price(c.get("current_price", 0))
        pct = c.get("price_change_percentage_24h", 0) or 0
        arrow = "🟢" if pct >= 0 else "🔴"
        sign = "+" if pct >= 0 else ""
        lines.append(f"{i:2}. {arrow} {sym:<7} {price:<13} <code>{sign}{pct:.2f}%</code>")

    lines.append("\n👇 Quyida tugmadan coin tanlang yoki nomini yozing:")
    return "\n".join(lines)


async def _send_top_three_messages(send_fn, edit_fn, chat_id, coins, context):
    """Overview + to'liq ro'yxat + barcha 99 tugma — 3 ta xabar."""
    text1 = _build_overview(coins)
    text2 = _build_full_list(coins)

    await edit_fn(text1, parse_mode=ParseMode.HTML, reply_markup=back_to_menu_keyboard())
    await context.bot.send_message(chat_id, text2, parse_mode=ParseMode.HTML)
    await context.bot.send_message(
        chat_id,
        "🔘 <b>Coin tanlang:</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=top_coins_keyboard(coins),
    )


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_keyboard(),
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=back_to_menu_keyboard(),
    )


async def top_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Binance top 99 coin yuklanmoqda...")
    try:
        coins = await get_top_binance_coins(99)
        await _send_top_three_messages(
            send_fn=update.message.reply_text,
            edit_fn=msg.edit_text,
            chat_id=update.message.chat_id,
            coins=coins,
            context=context,
        )
    except Exception as e:
        await msg.edit_text(f"❌ Xato: {e}", reply_markup=back_to_menu_keyboard())


async def coin_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "📝 Misol: <code>/coin bitcoin</code> yoki <code>/coin btc</code>",
            parse_mode=ParseMode.HTML,
        )
        return
    query = " ".join(context.args).strip().lower()
    msg = await update.message.reply_text(f"🔍 <b>{query}</b> qidirilmoqda...", parse_mode=ParseMode.HTML)
    await _send_coin_info(msg, query, edit=True)


async def _send_coin_info(msg, query: str, edit: bool = False):
    try:
        coin_id = await search_coin(query)
        if not coin_id:
            text = f"❌ <b>{query}</b> topilmadi. To'liq nom yozing (masalan: bitcoin, ethereum)."
            if edit:
                await msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=back_to_menu_keyboard())
            else:
                await msg.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=back_to_menu_keyboard())
            return

        coin = await get_coin_by_id(coin_id)
        if not coin:
            text = "❌ Coin ma'lumotlari topilmadi."
            if edit:
                await msg.edit_text(text, parse_mode=ParseMode.HTML)
            else:
                await msg.reply_text(text, parse_mode=ParseMode.HTML)
            return

        card = _build_coin_card(coin)
        if edit:
            await msg.edit_text(card, parse_mode=ParseMode.HTML, reply_markup=coin_detail_keyboard(coin_id))
        else:
            await msg.reply_text(card, parse_mode=ParseMode.HTML, reply_markup=coin_detail_keyboard(coin_id))
    except Exception as e:
        text = f"❌ Xato yuz berdi: {e}"
        if edit:
            await msg.edit_text(text, reply_markup=back_to_menu_keyboard())
        else:
            await msg.reply_text(text, reply_markup=back_to_menu_keyboard())


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=WELCOME_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard(),
        )

    elif data == "top_coins":
        await query.edit_message_text("⏳ Binance top 99 coin yuklanmoqda...", parse_mode=ParseMode.HTML)
        try:
            coins = await get_top_binance_coins(99)
            await _send_top_three_messages(
                send_fn=query.message.reply_text,
                edit_fn=query.edit_message_text,
                chat_id=query.message.chat_id,
                coins=coins,
                context=context,
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Xato: {e}", reply_markup=back_to_menu_keyboard())

    elif data == "gainers_24h":
        await query.edit_message_text("⏳ Oshganlar yuklanmoqda...", parse_mode=ParseMode.HTML)
        try:
            coins = await get_top_binance_coins(99)
            gainers = sorted(
                [c for c in coins if (c.get("price_change_percentage_24h") or 0) >= 0],
                key=lambda c: c.get("price_change_percentage_24h") or 0,
                reverse=True,
            )
            lines = [f"🟢 <b>OSHGANLAR — so'nggi 24 soat ({len(gainers)} ta coin)</b>\n"]
            for i, c in enumerate(gainers, 1):
                sym = c.get("symbol", "").upper()
                pct = c.get("price_change_percentage_24h", 0) or 0
                price = format_price(c.get("current_price", 0))
                lines.append(f"{i:2}. 🟢 {sym:<7} <code>+{pct:.2f}%</code>  {price}")
            lines.append("\n👇 Coin tanlang:")
            await query.edit_message_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=back_to_menu_keyboard())
            await context.bot.send_message(
                query.message.chat_id,
                "🔘 <b>Coin tanlang:</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=top_coins_keyboard(gainers),
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Xato: {e}", reply_markup=back_to_menu_keyboard())

    elif data == "losers_24h":
        await query.edit_message_text("⏳ Tushganlar yuklanmoqda...", parse_mode=ParseMode.HTML)
        try:
            coins = await get_top_binance_coins(99)
            losers = sorted(
                [c for c in coins if (c.get("price_change_percentage_24h") or 0) < 0],
                key=lambda c: c.get("price_change_percentage_24h") or 0,
            )
            lines = [f"🔴 <b>TUSHGANLAR — so'nggi 24 soat ({len(losers)} ta coin)</b>\n"]
            for i, c in enumerate(losers, 1):
                sym = c.get("symbol", "").upper()
                pct = c.get("price_change_percentage_24h", 0) or 0
                price = format_price(c.get("current_price", 0))
                lines.append(f"{i:2}. 🔴 {sym:<7} <code>{pct:.2f}%</code>  {price}")
            lines.append("\n👇 Coin tanlang:")
            await query.edit_message_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=back_to_menu_keyboard())
            await context.bot.send_message(
                query.message.chat_id,
                "🔘 <b>Coin tanlang:</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=top_coins_keyboard(losers),
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Xato: {e}", reply_markup=back_to_menu_keyboard())

    elif data == "help":
        await query.edit_message_text(HELP_TEXT, parse_mode=ParseMode.HTML, reply_markup=back_to_menu_keyboard())

    elif data.startswith("coin_"):
        # Yangi xabar yuborish — yuqoridagi 99 tugmali xabar o'zgarishsiz qoladi
        coin_id = data[5:]
        loading = await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="⏳ Ma'lumot yuklanmoqda...",
        )
        try:
            coin = await get_coin_by_id(coin_id)
            if not coin:
                await loading.edit_text("❌ Topilmadi.", reply_markup=back_to_menu_keyboard())
                return
            card = _build_coin_card(coin)
            await loading.edit_text(card, parse_mode=ParseMode.HTML, reply_markup=coin_detail_keyboard(coin_id))
        except Exception as e:
            await loading.edit_text(f"❌ Xato: {e}", reply_markup=back_to_menu_keyboard())

    elif data.startswith("analyze_"):
        coin_id = data[8:]
        await query.edit_message_text("🤖 AI tahlil qilinmoqda... ⏳", parse_mode=ParseMode.HTML)
        try:
            coin = await get_coin_by_id(coin_id)
            if not coin:
                await query.edit_message_text("❌ Topilmadi.", reply_markup=back_to_menu_keyboard())
                return
            card = _build_coin_card(coin)
            ai_text = await analyze_coin(_coin_data_for_ai(coin))
            full_text = card + f"\n🤖 <b>AI Tahlil:</b>\n{ai_text}"
            await query.edit_message_text(full_text, parse_mode=ParseMode.HTML, reply_markup=coin_detail_keyboard(coin_id))
        except Exception as e:
            await query.edit_message_text(f"❌ Xato: {e}", reply_markup=back_to_menu_keyboard())

    elif data.startswith("refresh_"):
        coin_id = data[8:]
        await query.edit_message_text("🔄 Yangilanmoqda...", parse_mode=ParseMode.HTML)
        try:
            coin = await get_coin_by_id(coin_id)
            if not coin:
                await query.edit_message_text("❌ Topilmadi.", reply_markup=back_to_menu_keyboard())
                return
            card = _build_coin_card(coin)
            await query.edit_message_text(card, parse_mode=ParseMode.HTML, reply_markup=coin_detail_keyboard(coin_id))
        except Exception as e:
            await query.edit_message_text(f"❌ Xato: {e}", reply_markup=back_to_menu_keyboard())


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi matn yuborsa — coin qidirish."""
    if context.user_data.get("awaiting_coin_search"):
        context.user_data["awaiting_coin_search"] = False
        query_text = update.message.text.strip().lower()
        msg = await update.message.reply_text(f"🔍 <b>{query_text}</b> qidirilmoqda...", parse_mode=ParseMode.HTML)
        await _send_coin_info(msg, query_text, edit=True)
    else:
        query_text = update.message.text.strip().lower()
        msg = await update.message.reply_text(f"🔍 <b>{query_text}</b> qidirilmoqda...", parse_mode=ParseMode.HTML)
        await _send_coin_info(msg, query_text, edit=True)
