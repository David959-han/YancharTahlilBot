import httpx
from config import BINANCE_BASE_URL, STABLECOIN_SYMBOLS

# Binance symbol → CoinGecko ID (individual coin detail uchun)
_SYMBOL_TO_CG = {
    "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin",
    "SOL": "solana", "XRP": "ripple", "DOGE": "dogecoin",
    "ADA": "cardano", "AVAX": "avalanche-2", "LINK": "chainlink",
    "DOT": "polkadot", "TRX": "tron", "TON": "the-open-network",
    "SHIB": "shiba-inu", "SUI": "sui", "LTC": "litecoin",
    "BCH": "bitcoin-cash", "APT": "aptos", "NEAR": "near",
    "UNI": "uniswap", "ICP": "internet-computer", "OP": "optimism",
    "ARB": "arbitrum", "INJ": "injective-protocol", "ATOM": "cosmos",
    "ETC": "ethereum-classic", "XLM": "stellar", "FIL": "filecoin",
    "VET": "vechain", "HBAR": "hedera-hashgraph", "STX": "blockstack",
    "MKR": "maker", "AAVE": "aave", "GRT": "the-graph",
    "ALGO": "algorand", "LDO": "lido-dao", "FTM": "fantom",
    "SEI": "sei-network", "TIA": "celestia", "RUNE": "thorchain",
    "WLD": "worldcoin-wld", "PEPE": "pepe", "FLOKI": "floki",
    "BONK": "bonk", "WIF": "dogwifcoin", "ENA": "ethena",
    "NOT": "notcoin", "GMT": "stepn", "AR": "arweave",
    "BLUR": "blur", "DYDX": "dydx-chain", "CFX": "conflux-token",
    "EGLD": "elrond-erd-2", "KSM": "kusama", "FLOW": "flow",
    "XTZ": "tezos", "THETA": "theta-token", "1INCH": "1inch",
    "SNX": "synthetix-network-token", "CRV": "curve-dao-token",
    "COMP": "compound-governance-token", "YFI": "yearn-finance",
    "SUSHI": "sushi", "BAND": "band-protocol", "ENS": "ethereum-name-service",
    "IMX": "immutable-x", "RPL": "rocket-pool", "GALA": "gala",
    "AXS": "axie-infinity", "SAND": "the-sandbox", "MANA": "decentraland",
    "ROSE": "oasis-network", "ONE": "harmony", "KAVA": "kava",
    "ANKR": "ankr", "IOTX": "iotex", "ZEC": "zcash", "DASH": "dash",
    "CHZ": "chiliz", "ZIL": "zilliqa", "BAT": "basic-attention-token",
    "IOTA": "iota", "QTUM": "qtum", "ONT": "ontology", "WAVES": "waves",
    "ICX": "icon", "HOT": "holotoken", "MINA": "mina-protocol",
    "FLR": "flare-networks", "STRK": "starknet", "EIGEN": "eigenlayer",
    "PENDLE": "pendle", "MANTA": "manta-network", "JUP": "jupiter-exchange-solana",
    "PYTH": "pyth-network", "ZRO": "layerzero", "ONDO": "ondo-finance",
    "WOO": "woo-network", "SC": "siacoin", "RVN": "ravencoin",
    "CELO": "celo", "BEAM": "beam-2", "NEO": "neo",
    "MOVE": "movement", "VIRTUAL": "virtual-protocol",
}


COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"


async def get_top_binance_coins(n: int = 99) -> list[dict]:
    """CoinGecko orqali top N coin (hajm bo'yicha, stablecoinsiz)."""
    params = {
        "vs_currency": "usd",
        "order": "volume_desc",
        "per_page": 150,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(COINGECKO_URL, params=params, timeout=20)
        resp.raise_for_status()
        coins = resp.json()

    result = []
    for c in coins:
        sym = (c.get("symbol") or "").lower()
        if sym in STABLECOIN_SYMBOLS:
            continue
        if not sym.isascii() or not sym.isalpha():
            continue
        result.append({
            "id": c["id"],
            "symbol": sym,
            "name": c.get("name", sym.upper()),
            "current_price": c.get("current_price") or 0,
            "price_change_percentage_24h": c.get("price_change_percentage_24h") or 0,
            "total_volume": c.get("total_volume") or 0,
            "high_24h": c.get("high_24h") or 0,
            "low_24h": c.get("low_24h") or 0,
            "market_cap": c.get("market_cap") or 0,
            "price_change_percentage_1h": None,
            "price_change_percentage_7d": None,
        })
        if len(result) >= n:
            break

    return result
