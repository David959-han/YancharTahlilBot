import time
import asyncio
import httpx
from config import COINGECKO_BASE_URL, TOP_COINS_COUNT, STABLECOIN_SYMBOLS

_cache: dict = {}
_CACHE_TTL = 60  # sekund


def is_real_coin(coin: dict) -> bool:
    symbol = coin.get("symbol", "")
    # Stablecoin yoki ASCII bo'lmagan belgilar (xitoy, arab harflari)
    if not symbol.isascii() or not symbol.replace("_", "").isalnum():
        return False
    return symbol.lower() not in STABLECOIN_SYMBOLS


def get_gainers(coins: list, n: int = 5) -> list:
    real = [c for c in coins if is_real_coin(c)]
    return sorted(real, key=lambda c: c.get("price_change_percentage_24h") or 0, reverse=True)[:n]


def get_losers(coins: list, n: int = 5) -> list:
    real = [c for c in coins if is_real_coin(c)]
    return sorted(real, key=lambda c: c.get("price_change_percentage_24h") or 0)[:n]


def get_real_coins(coins: list) -> list:
    return [c for c in coins if is_real_coin(c)]


async def get_top_coins() -> list[dict]:
    url = f"{COINGECKO_BASE_URL}/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": TOP_COINS_COUNT,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()


async def get_coin_by_id(coin_id: str) -> dict | None:
    # Keshdan qaytarish
    if coin_id in _cache:
        data, ts = _cache[coin_id]
        if time.time() - ts < _CACHE_TTL:
            return data

    url = f"{COINGECKO_BASE_URL}/coins/{coin_id}"
    params = {
        "localization": False,
        "tickers": False,
        "market_data": True,
        "community_data": False,
        "developer_data": False,
    }

    # 429 bo'lsa 2 marta qayta urinish
    for attempt in range(3):
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)
        if response.status_code == 429:
            await asyncio.sleep(2 ** attempt)
            continue
        if response.status_code == 404:
            return None
        response.raise_for_status()
        break
    else:
        raise Exception("CoinGecko so'rovlar limiti tugadi, bir oz kuting.")

    data = response.json()
    market = data.get("market_data", {})
    result = {
        "id": data["id"],
        "name": data["name"],
        "symbol": data["symbol"].upper(),
        "current_price": market.get("current_price", {}).get("usd", 0),
        "market_cap": market.get("market_cap", {}).get("usd", 0),
        "total_volume": market.get("total_volume", {}).get("usd", 0),
        "price_change_percentage_1h": market.get("price_change_percentage_1h_in_currency", {}).get("usd", 0),
        "price_change_percentage_24h": market.get("price_change_percentage_24h_in_currency", {}).get("usd", 0),
        "price_change_percentage_7d": market.get("price_change_percentage_7d_in_currency", {}).get("usd", 0),
        "high_24h": market.get("high_24h", {}).get("usd", 0),
        "low_24h": market.get("low_24h", {}).get("usd", 0),
        "ath": market.get("ath", {}).get("usd", 0),
        "ath_change_percentage": market.get("ath_change_percentage", {}).get("usd", 0),
    }
    _cache[coin_id] = (result, time.time())
    return result


async def search_coin(query: str) -> str | None:
    url = f"{COINGECKO_BASE_URL}/search"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params={"query": query}, timeout=10)
        response.raise_for_status()
        results = response.json().get("coins", [])
        return results[0]["id"] if results else None


def format_price(price: float) -> str:
    if price >= 1000:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:.4f}".rstrip("0").rstrip(".")
    elif price >= 0.01:
        return f"${price:.4f}"
    elif price >= 0.0001:
        return f"${price:.6f}"
    else:
        return f"${price:.8f}"


def format_market_cap(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,.0f}"


def format_change(pct: float) -> str:
    if pct is None:
        return "N/A"
    arrow = "🟢" if pct >= 0 else "🔴"
    sign = "+" if pct >= 0 else ""
    return f"{arrow} {sign}{pct:.2f}%"
