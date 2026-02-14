"""Market data module using yfinance for price data and historical performance."""

import logging
from datetime import datetime, timedelta

import yfinance as yf

logger = logging.getLogger(__name__)


def get_daily_summary(ticker: str) -> dict | None:
    """Get today's price summary for a ticker.

    Returns:
        dict with keys: open, high, low, close, prev_close, change, change_pct, volume
        None if data unavailable.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if hist.empty or len(hist) < 1:
            logger.warning("No recent data for %s", ticker)
            return None

        latest = hist.iloc[-1]
        prev_close = hist.iloc[-2]["Close"] if len(hist) >= 2 else latest["Open"]
        change = latest["Close"] - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0

        return {
            "open": round(latest["Open"], 2),
            "high": round(latest["High"], 2),
            "low": round(latest["Low"], 2),
            "close": round(latest["Close"], 2),
            "prev_close": round(prev_close, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "volume": int(latest["Volume"]),
        }
    except Exception as e:
        logger.error("Failed to get daily summary for %s: %s", ticker, e)
        return None


def get_6month_performance(ticker: str) -> dict | None:
    """Get 6-month performance metrics for a ticker.

    Returns:
        dict with keys: start_price, end_price, change, change_pct,
                        high_6m, low_6m, avg_volume
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        if hist.empty or len(hist) < 2:
            logger.warning("Insufficient 6-month data for %s", ticker)
            return None

        start_price = hist.iloc[0]["Close"]
        end_price = hist.iloc[-1]["Close"]
        change = end_price - start_price
        change_pct = (change / start_price) * 100 if start_price else 0

        return {
            "start_price": round(start_price, 2),
            "end_price": round(end_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "high_6m": round(hist["High"].max(), 2),
            "low_6m": round(hist["Low"].min(), 2),
            "avg_volume": int(hist["Volume"].mean()),
            "start_date": hist.index[0].strftime("%Y-%m-%d"),
            "end_date": hist.index[-1].strftime("%Y-%m-%d"),
        }
    except Exception as e:
        logger.error("Failed to get 6-month performance for %s: %s", ticker, e)
        return None


def get_batch_daily(tickers: list[str]) -> dict[str, dict]:
    """Get daily summaries for multiple tickers.

    Returns a dict mapping ticker -> daily summary.
    """
    results = {}
    for ticker in tickers:
        summary = get_daily_summary(ticker)
        if summary:
            results[ticker] = summary
    return results


def get_batch_6month(tickers: list[str]) -> dict[str, dict]:
    """Get 6-month performance for multiple tickers.

    Returns a dict mapping ticker -> 6-month performance.
    """
    results = {}
    for ticker in tickers:
        perf = get_6month_performance(ticker)
        if perf:
            results[ticker] = perf
    return results
