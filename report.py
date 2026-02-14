"""End-of-day report generator combining portfolio, market data, and news."""

import logging
from datetime import datetime

from tabulate import tabulate

import market_data
import news

logger = logging.getLogger(__name__)

UP_ARROW = "▲"
DOWN_ARROW = "▼"
NEUTRAL = "─"


def _direction_symbol(change: float) -> str:
    if change > 0:
        return UP_ARROW
    elif change < 0:
        return DOWN_ARROW
    return NEUTRAL


def _format_change(change: float, change_pct: float) -> str:
    symbol = _direction_symbol(change)
    sign = "+" if change >= 0 else ""
    return f"{symbol} {sign}{change:.2f} ({sign}{change_pct:.2f}%)"


def generate_report(
    portfolio: list[dict],
    watchlist: list[str],
    include_news: bool = True,
) -> str:
    """Generate a full end-of-day report.

    Args:
        portfolio: List of position dicts from Trading 212 (with 'ticker' key).
        watchlist: List of watchlist ticker symbols.
        include_news: Whether to include news section.

    Returns:
        Formatted report string.
    """
    all_tickers = list({p["ticker"] for p in portfolio} | set(watchlist))
    portfolio_tickers = [p["ticker"] for p in portfolio]

    # Fetch all market data
    logger.info("Fetching daily data for %d tickers...", len(all_tickers))
    daily_data = market_data.get_batch_daily(all_tickers)

    logger.info("Fetching 6-month performance...")
    perf_data = market_data.get_batch_6month(all_tickers)

    sections = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    sections.append(f"{'=' * 70}")
    sections.append(f"  TRADING 212 STOCK TRACKER - END OF DAY REPORT")
    sections.append(f"  Generated: {now}")
    sections.append(f"{'=' * 70}")

    # --- Portfolio Section ---
    if portfolio:
        sections.append(f"\n{'─' * 70}")
        sections.append("  PORTFOLIO POSITIONS")
        sections.append(f"{'─' * 70}")

        table_rows = []
        total_invested = 0
        total_ppl = 0

        for pos in portfolio:
            ticker = pos["ticker"]
            daily = daily_data.get(ticker, {})
            change = daily.get("change", 0)
            change_pct = daily.get("change_pct", 0)

            table_rows.append([
                ticker,
                pos.get("quantity", 0),
                f"{pos.get('avg_price', 0):.2f}",
                f"{daily.get('close', pos.get('current_price', 0)):.2f}",
                _format_change(change, change_pct),
                f"{pos.get('ppl', 0):+.2f}",
            ])
            total_invested += pos.get("avg_price", 0) * pos.get("quantity", 0)
            total_ppl += pos.get("ppl", 0)

        sections.append(tabulate(
            table_rows,
            headers=["Ticker", "Qty", "Avg Price", "Close", "Day Change", "P&L"],
            tablefmt="simple",
            numalign="right",
        ))

        sections.append(f"\n  Total Invested: {total_invested:,.2f}")
        sections.append(f"  Total P&L:      {total_ppl:+,.2f}")

    # --- Watchlist Section ---
    if watchlist:
        sections.append(f"\n{'─' * 70}")
        sections.append("  WATCHLIST")
        sections.append(f"{'─' * 70}")

        table_rows = []
        for ticker in sorted(watchlist):
            daily = daily_data.get(ticker, {})
            if not daily:
                table_rows.append([ticker, "N/A", "N/A", "N/A", "No data"])
                continue

            change = daily.get("change", 0)
            change_pct = daily.get("change_pct", 0)
            table_rows.append([
                ticker,
                f"{daily.get('open', 0):.2f}",
                f"{daily.get('close', 0):.2f}",
                f"{daily.get('volume', 0):,}",
                _format_change(change, change_pct),
            ])

        sections.append(tabulate(
            table_rows,
            headers=["Ticker", "Open", "Close", "Volume", "Day Change"],
            tablefmt="simple",
            numalign="right",
        ))

    # --- 6-Month Performance Section ---
    sections.append(f"\n{'─' * 70}")
    sections.append("  6-MONTH PERFORMANCE")
    sections.append(f"{'─' * 70}")

    table_rows = []
    for ticker in sorted(all_tickers):
        perf = perf_data.get(ticker)
        if not perf:
            table_rows.append([ticker, "N/A", "N/A", "N/A", "N/A", "N/A"])
            continue

        change_pct = perf["change_pct"]
        table_rows.append([
            ticker,
            f"{perf['start_price']:.2f}",
            f"{perf['end_price']:.2f}",
            _format_change(perf["change"], change_pct),
            f"{perf['high_6m']:.2f}",
            f"{perf['low_6m']:.2f}",
        ])

    sections.append(tabulate(
        table_rows,
        headers=["Ticker", "6M Start", "Current", "6M Change", "6M High", "6M Low"],
        tablefmt="simple",
        numalign="right",
    ))

    # --- Buy Signal Hints ---
    sections.append(f"\n{'─' * 70}")
    sections.append("  BUYING SIGNALS SUMMARY")
    sections.append(f"{'─' * 70}")

    for ticker in sorted(all_tickers):
        daily = daily_data.get(ticker)
        perf = perf_data.get(ticker)
        if not daily or not perf:
            continue

        signals = []
        in_portfolio = ticker in portfolio_tickers

        # Near 6-month low (within 5%)
        if perf["low_6m"] > 0:
            pct_above_low = ((daily["close"] - perf["low_6m"]) / perf["low_6m"]) * 100
            if pct_above_low <= 5:
                signals.append(f"Near 6M low ({pct_above_low:.1f}% above)")

        # Significant daily dip (down > 3%)
        if daily["change_pct"] <= -3:
            signals.append(f"Significant daily dip ({daily['change_pct']:.1f}%)")

        # 6-month downtrend but recent uptick
        if perf["change_pct"] < -10 and daily["change_pct"] > 0:
            signals.append("Potential reversal (6M down, today up)")

        # Strong 6-month growth (over 20%)
        if perf["change_pct"] > 20:
            signals.append(f"Strong 6M momentum (+{perf['change_pct']:.1f}%)")

        # Near 6-month high (within 3%) - caution signal
        if perf["high_6m"] > 0:
            pct_below_high = ((perf["high_6m"] - daily["close"]) / perf["high_6m"]) * 100
            if pct_below_high <= 3:
                signals.append(f"Near 6M high ({pct_below_high:.1f}% below) - caution")

        if signals:
            label = "[HELD]" if in_portfolio else "[WATCH]"
            sections.append(f"\n  {label} {ticker}:")
            for s in signals:
                sections.append(f"    - {s}")

    # --- News Section ---
    if include_news:
        sections.append(f"\n{'─' * 70}")
        sections.append("  MARKET NEWS")
        sections.append(f"{'─' * 70}")

        all_news = news.get_batch_news(all_tickers, days_back=3)
        if all_news:
            for ticker in sorted(all_news.keys()):
                articles = all_news[ticker]
                sections.append(f"\n  {ticker}:")
                for article in articles[:3]:  # Top 3 per ticker
                    sections.append(f"    [{article['datetime']}] {article['headline']}")
                    sections.append(f"      Source: {article['source']}")
                    if article.get("url"):
                        sections.append(f"      {article['url']}")
        else:
            sections.append("  No news available (check Finnhub API key)")

        # General market news
        general = news.get_market_news()
        if general:
            sections.append(f"\n  GENERAL MARKET:")
            for article in general[:5]:
                sections.append(f"    [{article['datetime']}] {article['headline']}")
                sections.append(f"      Source: {article['source']}")

    sections.append(f"\n{'=' * 70}")
    sections.append(f"  END OF REPORT")
    sections.append(f"{'=' * 70}\n")

    return "\n".join(sections)
