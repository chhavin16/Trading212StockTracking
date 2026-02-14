"""News module using Finnhub for stock-specific market news."""

import logging
from datetime import datetime, timedelta

import finnhub

import config

logger = logging.getLogger(__name__)


def _get_client() -> finnhub.Client | None:
    """Create a Finnhub API client."""
    if not config.FINNHUB_API_KEY:
        logger.warning("Finnhub API key not configured")
        return None
    return finnhub.Client(api_key=config.FINNHUB_API_KEY)


def get_company_news(ticker: str, days_back: int = 3) -> list[dict]:
    """Fetch recent news articles for a specific company.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL").
        days_back: Number of days to look back for news.

    Returns:
        List of dicts with keys: headline, summary, source, url, datetime.
    """
    client = _get_client()
    if not client:
        return []

    today = datetime.now()
    from_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")

    try:
        raw_news = client.company_news(ticker, _from=from_date, to=to_date)
        articles = []
        for article in raw_news[:5]:  # Limit to 5 most recent
            articles.append({
                "headline": article.get("headline", ""),
                "summary": article.get("summary", ""),
                "source": article.get("source", ""),
                "url": article.get("url", ""),
                "datetime": datetime.fromtimestamp(
                    article.get("datetime", 0)
                ).strftime("%Y-%m-%d %H:%M"),
            })
        return articles
    except Exception as e:
        logger.error("Failed to get news for %s: %s", ticker, e)
        return []


def get_market_news() -> list[dict]:
    """Fetch general market news.

    Returns:
        List of dicts with keys: headline, summary, source, url, datetime.
    """
    client = _get_client()
    if not client:
        return []

    try:
        raw_news = client.general_news("general", min_id=0)
        articles = []
        for article in raw_news[:10]:  # Top 10 general news
            articles.append({
                "headline": article.get("headline", ""),
                "summary": article.get("summary", ""),
                "source": article.get("source", ""),
                "url": article.get("url", ""),
                "datetime": datetime.fromtimestamp(
                    article.get("datetime", 0)
                ).strftime("%Y-%m-%d %H:%M"),
            })
        return articles
    except Exception as e:
        logger.error("Failed to get market news: %s", e)
        return []


def get_batch_news(tickers: list[str], days_back: int = 3) -> dict[str, list[dict]]:
    """Fetch news for multiple tickers.

    Returns a dict mapping ticker -> list of news articles.
    """
    results = {}
    for ticker in tickers:
        articles = get_company_news(ticker, days_back)
        if articles:
            results[ticker] = articles
    return results
