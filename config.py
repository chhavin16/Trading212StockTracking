import os
import json
from dotenv import load_dotenv

load_dotenv()

# Trading 212
TRADING212_API_KEY = os.getenv("TRADING212_API_KEY", "")
TRADING212_API_SECRET = os.getenv("TRADING212_API_SECRET", "")
TRADING212_ENV = os.getenv("TRADING212_ENV", "live")

TRADING212_BASE_URLS = {
    "live": "https://live.trading212.com/api/v0",
    "demo": "https://demo.trading212.com/api/v0",
}
TRADING212_BASE_URL = TRADING212_BASE_URLS.get(TRADING212_ENV, TRADING212_BASE_URLS["live"])

# Finnhub
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")

# Watchlist file path
WATCHLIST_PATH = os.path.join(os.path.dirname(__file__), "watchlist.json")


def load_watchlist() -> list[str]:
    """Load watchlist tickers from watchlist.json."""
    try:
        with open(WATCHLIST_PATH) as f:
            data = json.load(f)
        return data.get("watchlist", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_watchlist(tickers: list[str]) -> None:
    """Save watchlist tickers to watchlist.json."""
    data = {
        "description": "Stocks you want to track that are NOT in your Trading 212 portfolio. Add ticker symbols here.",
        "watchlist": sorted(set(tickers)),
    }
    with open(WATCHLIST_PATH, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
