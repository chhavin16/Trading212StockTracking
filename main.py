#!/usr/bin/env python3
"""Trading 212 Stock Tracker - End of Day Report Tool.

Tracks your Trading 212 portfolio positions and watchlist stocks,
providing daily summaries, 6-month performance, market news, and
buying signal hints.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime

import config
import market_data
import news
import report
import trading212


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_report(args: argparse.Namespace) -> None:
    """Generate and display the end-of-day report."""
    # Fetch portfolio from Trading 212
    portfolio = []
    if config.TRADING212_API_KEY and config.TRADING212_API_SECRET:
        logging.info("Fetching portfolio from Trading 212...")
        portfolio = trading212.get_positions()
        if portfolio:
            logging.info("Found %d positions", len(portfolio))
        else:
            logging.warning("No positions returned from Trading 212")
    else:
        logging.warning(
            "Trading 212 API credentials not set. "
            "Only watchlist stocks will be tracked. "
            "Set TRADING212_API_KEY and TRADING212_API_SECRET in .env"
        )

    # Load watchlist
    watchlist = config.load_watchlist()
    logging.info("Watchlist: %d tickers", len(watchlist))

    if not portfolio and not watchlist:
        print("No stocks to track. Either:")
        print("  1. Configure Trading 212 API credentials in .env")
        print("  2. Add tickers to watchlist.json")
        print("  3. Run: python main.py watchlist add AAPL MSFT GOOGL")
        sys.exit(1)

    # Generate report
    output = report.generate_report(
        portfolio=portfolio,
        watchlist=watchlist,
        include_news=not args.no_news,
    )

    print(output)

    # Save report to file if requested
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Report saved to: {args.output}")


def cmd_watchlist(args: argparse.Namespace) -> None:
    """Manage the watchlist."""
    current = config.load_watchlist()

    if args.watchlist_action == "list":
        if current:
            print("Current watchlist:")
            for ticker in sorted(current):
                print(f"  - {ticker}")
        else:
            print("Watchlist is empty. Add tickers with: python main.py watchlist add AAPL MSFT")

    elif args.watchlist_action == "add":
        tickers = [t.upper() for t in args.tickers]
        updated = sorted(set(current) | set(tickers))
        config.save_watchlist(updated)
        added = set(tickers) - set(current)
        if added:
            print(f"Added: {', '.join(sorted(added))}")
        already = set(tickers) & set(current)
        if already:
            print(f"Already in watchlist: {', '.join(sorted(already))}")

    elif args.watchlist_action == "remove":
        tickers = [t.upper() for t in args.tickers]
        updated = sorted(set(current) - set(tickers))
        config.save_watchlist(updated)
        removed = set(tickers) & set(current)
        if removed:
            print(f"Removed: {', '.join(sorted(removed))}")
        not_found = set(tickers) - set(current)
        if not_found:
            print(f"Not in watchlist: {', '.join(sorted(not_found))}")


def cmd_quick(args: argparse.Namespace) -> None:
    """Quick check on a specific ticker."""
    ticker = args.ticker.upper()
    print(f"Quick check: {ticker}\n")

    daily = market_data.get_daily_summary(ticker)
    if daily:
        change_sign = "+" if daily["change"] >= 0 else ""
        print(f"  Today:  Open {daily['open']}  |  Close {daily['close']}  |  "
              f"Change {change_sign}{daily['change']} ({change_sign}{daily['change_pct']}%)")
        print(f"  Range:  Low {daily['low']}  |  High {daily['high']}  |  "
              f"Volume {daily['volume']:,}")
    else:
        print(f"  No daily data available for {ticker}")

    perf = market_data.get_6month_performance(ticker)
    if perf:
        change_sign = "+" if perf["change"] >= 0 else ""
        print(f"\n  6-Month ({perf['start_date']} to {perf['end_date']}):")
        print(f"  Start {perf['start_price']}  |  Current {perf['end_price']}  |  "
              f"Change {change_sign}{perf['change']} ({change_sign}{perf['change_pct']}%)")
        print(f"  6M High {perf['high_6m']}  |  6M Low {perf['low_6m']}")

    if not args.no_news:
        articles = news.get_company_news(ticker)
        if articles:
            print(f"\n  Recent News:")
            for a in articles[:3]:
                print(f"    [{a['datetime']}] {a['headline']}")
                print(f"      {a['source']}")
        elif not config.FINNHUB_API_KEY:
            print(f"\n  News unavailable (set FINNHUB_API_KEY in .env)")

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trading 212 Stock Tracker - End of Day Report Tool",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    subparsers = parser.add_subparsers(dest="command")

    # report command
    report_parser = subparsers.add_parser("report", help="Generate end-of-day report")
    report_parser.add_argument(
        "-o", "--output", help="Save report to file (e.g., reports/report.txt)"
    )
    report_parser.add_argument(
        "--no-news", action="store_true", help="Skip news section"
    )

    # watchlist command
    wl_parser = subparsers.add_parser("watchlist", help="Manage watchlist")
    wl_subparsers = wl_parser.add_subparsers(dest="watchlist_action")

    wl_list = wl_subparsers.add_parser("list", help="Show watchlist")
    wl_add = wl_subparsers.add_parser("add", help="Add tickers to watchlist")
    wl_add.add_argument("tickers", nargs="+", help="Ticker symbols to add")
    wl_remove = wl_subparsers.add_parser("remove", help="Remove tickers from watchlist")
    wl_remove.add_argument("tickers", nargs="+", help="Ticker symbols to remove")

    # quick command
    quick_parser = subparsers.add_parser("quick", help="Quick check on a single ticker")
    quick_parser.add_argument("ticker", help="Ticker symbol")
    quick_parser.add_argument(
        "--no-news", action="store_true", help="Skip news"
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.command == "report":
        cmd_report(args)
    elif args.command == "watchlist":
        if not args.watchlist_action:
            wl_parser.print_help()
        else:
            cmd_watchlist(args)
    elif args.command == "quick":
        cmd_quick(args)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python main.py report                    # Full end-of-day report")
        print("  python main.py report --no-news          # Report without news")
        print("  python main.py report -o report.txt      # Save report to file")
        print("  python main.py watchlist list             # Show watchlist")
        print("  python main.py watchlist add TSLA NVDA    # Add to watchlist")
        print("  python main.py watchlist remove GOOGL     # Remove from watchlist")
        print("  python main.py quick AAPL                 # Quick check on a ticker")


if __name__ == "__main__":
    main()
