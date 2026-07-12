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


def _base(binance_sym: str) -> str:
    return binance_sym[:-4] if binance_sym.endswith("USDT") else binance_sym


async def get_top_binance_coins(n: int = 99) -> list[dict]:
    """Binance USDT spot juftliklari, 24s savdo hajmi bo'yicha top N."""
    url = f"{BINANCE_BASE_URL}/ticker/24hr"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=20)
        resp.raise_for_status()
        tickers = resp.json()

    valid = []
    for t in tickers:
        if not t["symbol"].endswith("USDT"):
            continue
        base = _base(t["symbol"])
        if (
            base.isascii()
            and base.isalpha()
            and 2 <= len(base) <= 10
            and base.lower() not in STABLECOIN_SYMBOLS
        ):
            valid.append(t)

    valid.sort(key=lambda t: float(t["quoteVolume"]), reverse=True)

    result = []
    for t in valid[:n]:
        base = _base(t["symbol"])
        cg_id = _SYMBOL_TO_CG.get(base.upper(), base.lower())
        result.append({
            "id": cg_id,
            "symbol": base.lower(),
            "name": base,
            "current_price": float(t["lastPrice"]),
            "price_change_percentage_24h": float(t["priceChangePercent"]),
            "total_volume": float(t["quoteVolume"]),
            "high_24h": float(t["highPrice"]),
            "low_24h": float(t["lowPrice"]),
            "market_cap": 0,
            "price_change_percentage_1h": None,
            "price_change_percentage_7d": None,
        })

    return result
