"""Trading 212 API client for fetching portfolio positions."""

import base64
import logging
import time

import requests

import config

logger = logging.getLogger(__name__)

# Mapping of common Trading 212 ticker suffixes to Yahoo Finance suffixes.
# Trading 212 uses internal ticker formats like "AAPL_US_EQ" while Yahoo
# Finance uses exchange suffixes like ".L" for London.
T212_TO_YAHOO = {
    "_US_EQ": "",        # US equities -> no suffix on Yahoo
    "_EQ": "",           # Generic equities
    "_LSE_EQ": ".L",    # London Stock Exchange
    "_DE_EQ": ".DE",    # Germany / XETRA
    "_FR_EQ": ".PA",    # France / Euronext Paris
    "_NL_EQ": ".AS",    # Netherlands / Euronext Amsterdam
}


def _auth_header() -> dict:
    """Build Basic Auth header from API key and secret."""
    if not config.TRADING212_API_KEY or not config.TRADING212_API_SECRET:
        return {}
    creds = f"{config.TRADING212_API_KEY}:{config.TRADING212_API_SECRET}"
    encoded = base64.b64encode(creds.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def _get(endpoint: str) -> dict | list | None:
    """Make a GET request to the Trading 212 API with retry logic."""
    url = f"{config.TRADING212_BASE_URL}{endpoint}"
    headers = _auth_header()
    if not headers:
        logger.warning("Trading 212 API credentials not configured")
        return None

    for attempt in range(4):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            remaining = resp.headers.get("x-ratelimit-remaining")
            if remaining is not None and int(remaining) <= 1:
                reset_ts = int(resp.headers.get("x-ratelimit-reset", 0))
                wait = max(0, reset_ts - int(time.time())) + 1
                logger.info("Rate limit approaching, sleeping %ds", wait)
                time.sleep(wait)

            if resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                logger.warning("Rate limited, retrying in %ds", wait)
                time.sleep(wait)
                continue

            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            if attempt < 3:
                wait = 2 ** (attempt + 1)
                logger.warning("Request failed (%s), retrying in %ds", e, wait)
                time.sleep(wait)
            else:
                logger.error("Request failed after 4 attempts: %s", e)
                return None
    return None


def t212_ticker_to_yahoo(t212_ticker: str) -> str:
    """Convert a Trading 212 ticker to a Yahoo Finance-compatible symbol.

    Examples:
        "AAPL_US_EQ" -> "AAPL"
        "BP_LSE_EQ"  -> "BP.L"
    """
    for suffix, yahoo_suffix in T212_TO_YAHOO.items():
        if t212_ticker.endswith(suffix):
            base = t212_ticker[: -len(suffix)]
            return f"{base}{yahoo_suffix}"
    # Fallback: strip everything after the first underscore
    return t212_ticker.split("_")[0]


def get_positions() -> list[dict]:
    """Fetch all open positions from Trading 212.

    Returns a list of dicts with keys:
        - ticker: Yahoo Finance-compatible ticker symbol
        - t212_ticker: original Trading 212 ticker
        - quantity: number of shares held
        - avg_price: average purchase price
        - current_price: latest price from Trading 212
        - ppl: profit/loss in account currency
    """
    data = _get("/equity/positions")
    if not data:
        return []

    positions = []
    for pos in data:
        t212_ticker = pos.get("ticker", "")
        positions.append({
            "ticker": t212_ticker_to_yahoo(t212_ticker),
            "t212_ticker": t212_ticker,
            "quantity": pos.get("quantity", 0),
            "avg_price": pos.get("averagePrice", 0),
            "current_price": pos.get("currentPrice", 0),
            "ppl": pos.get("ppl", 0),
        })
    return positions


def get_account_summary() -> dict | None:
    """Fetch account summary (balance, invested, result)."""
    return _get("/equity/account/cash")
