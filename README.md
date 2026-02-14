# Trading 212 Stock Tracker

End-of-day stock tracking tool for Trading 212 accounts. Pulls your portfolio positions directly from Trading 212, combines them with a local watchlist, and generates a daily report with price movements, 6-month performance, buying signal hints, and market news.

## What It Does

- **Portfolio tracking**: Fetches your open positions from Trading 212 via their official API
- **Watchlist**: Track additional stocks you're interested in buying (stored locally)
- **Daily summary**: Open, close, high, low, volume, and daily change for each stock
- **6-month performance**: Historical price range, percentage change, and trend
- **Buying signals**: Flags stocks near 6-month lows, significant dips, potential reversals, and strong momentum
- **Market news**: Company-specific and general market news via Finnhub

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your keys:

- **Trading 212**: Go to Trading 212 app > Settings > API Key. Generate a key with "Account data" and "Portfolio" permissions. You'll get an API key and a secret.
- **Finnhub**: Register for free at [finnhub.io](https://finnhub.io/register) to get an API key for stock news.

```
TRADING212_API_KEY=your_key
TRADING212_API_SECRET=your_secret
TRADING212_ENV=live
FINNHUB_API_KEY=your_finnhub_key
```

> **Note**: The app works without Trading 212 credentials — it will just track your watchlist stocks using yfinance. Finnhub is optional too (news section will be skipped).

### 3. Set up your watchlist

Edit `watchlist.json` directly, or use the CLI:

```bash
python main.py watchlist add AAPL MSFT TSLA NVDA
python main.py watchlist list
python main.py watchlist remove GOOGL
```

## Usage

### Full end-of-day report

```bash
python main.py report
```

### Report without news (faster)

```bash
python main.py report --no-news
```

### Save report to file

```bash
python main.py report -o reports/2024-01-15.txt
```

### Quick check on a single stock

```bash
python main.py quick AAPL
python main.py quick TSLA --no-news
```

### Verbose mode (debug logging)

```bash
python main.py -v report
```

## Report Sections

| Section | Data Source | API Key Required? |
|---------|-----------|-------------------|
| Portfolio Positions | Trading 212 API | Yes (Trading 212) |
| Watchlist | Local `watchlist.json` + yfinance | No |
| 6-Month Performance | yfinance | No |
| Buying Signals | Calculated from price data | No |
| Market News | Finnhub | Yes (Finnhub) |

## Buying Signals

The report flags potential buying opportunities based on simple heuristics:

- **Near 6M low**: Stock price is within 5% of its 6-month low
- **Significant daily dip**: Stock dropped more than 3% today
- **Potential reversal**: Stock is down >10% over 6 months but up today
- **Strong momentum**: Stock is up >20% over the last 6 months
- **Near 6M high (caution)**: Stock is within 3% of its 6-month high

These are informational signals, not financial advice. Always do your own research.

## Project Structure

```
├── main.py           # CLI entry point
├── config.py         # Configuration and env loading
├── trading212.py     # Trading 212 API client
├── market_data.py    # yfinance price data and history
├── news.py           # Finnhub news fetching
├── report.py         # Report generation and formatting
├── watchlist.json    # Your watchlist tickers
├── .env.example      # Template for API credentials
└── requirements.txt  # Python dependencies
```
