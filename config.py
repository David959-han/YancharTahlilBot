import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
BINANCE_BASE_URL = "https://api.binance.com/api/v3"

TOP_COINS_COUNT = 100

STABLECOIN_SYMBOLS = {
    "usdt", "usdc", "dai", "busd", "tusd", "usdp", "fdusd", "pyusd",
    "usds", "usdd", "usde", "usd1", "rlusd", "usdf", "usdtb", "usdg",
    "usdy", "usdgo", "usd0", "ustb", "ylds", "bfusd", "gho", "frax",
    "lusd", "susd", "gusd", "husd", "eurs", "eurt", "steur", "xaut",
    "paxg", "wbtc", "weth", "steth", "cbbtc", "buidl", "jaaa", "jtrsy",
    "eutbl", "eursafo", "usyc", "usx", "stable", "rain", "usdgo",
}
