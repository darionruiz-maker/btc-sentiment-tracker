# BTC Sentiment Tracker

A real-time Bitcoin market sentiment dashboard with actionable BUY/SELL/HOLD signals, built from 20+ technical indicators, backtested entry signals, whale transaction tracking, macro market correlation, and institutional holdings data.

![Dashboard Preview](https://img.shields.io/badge/status-live-brightgreen) ![Python](https://img.shields.io/badge/python-3.8%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

---

## What It Does

The dashboard answers one question: **Should I buy, sell, or hold Bitcoin right now?**

It combines data from 7 free APIs into a single composite score (-100 to +100) and a clear **BUY / SELL / HOLD** signal with confidence percentage and plain-English reasoning.

### Key Sections

| Section | What it shows |
|---|---|
| **Action Signal** | BUY / SELL / HOLD with confidence % and top 5 reasons |
| **Composite Score** | -100 (strong sell) to +100 (strong buy) needle gauge |
| **Rally Entry Signal** | Backtested checklist — only fires when 100% win-rate conditions are met |
| **Reversal Radar** | 9-signal bottom detection probability (0-95%) |
| **Macro Signals** | S&P 500, VIX, DXY, Gold, MSTR — is the broader market helping or hurting? |
| **Multi-Timeframe Trend** | Recent / Mid / Full Period / From High breakdown |
| **Price Chart** | With Bollinger Bands overlay |
| **Order Flow** | Live Kraken order book — buy/sell walls at each price level |
| **RSI** | Visual gauge + chart with oversold/overbought zones |
| **Whale Watch** | Large transactions (>10 BTC) from last 6 blocks with entity identification |
| **Institutional Holdings** | Public company BTC treasuries with cost basis and P&L vs current price |
| **Support & Resistance** | Auto-detected price levels from pivot points |
| **Indicator Agreement** | Bar showing how many of 20+ signals agree |
| **Time Machine** | Backtest — see what the dashboard would have predicted 1 week ago vs what actually happened |
| **Statistical Analysis** | Z-Score, Price Acceleration, Mean Reversion, VWAP, Volatility Squeeze, Price Percentile |

---

## Technical Indicators (20+)

| Indicator | Weight | What it detects |
|---|---|---|
| Period Change | 22 | Full timeframe price movement |
| Drawdown from High | 18 | How far from the peak |
| Market Structure | 18 | Lower highs / lower lows breakdown pattern |
| Trend Consistency | 14 | % of candles closing lower |
| Volume Confirmation | 12 | Volume confirms or denies the price move |
| RSI (14) | 12 | Overbought / oversold momentum |
| MACD | 10 | Momentum crossover signal |
| MA Cross | 10 | Short vs long moving average |
| Fear & Greed | 10 | Contrarian crowd sentiment |
| Rally Entry Signal | 20 | Backtested 7-condition entry checklist |
| Bollinger %B | 8 | Position within volatility bands |
| Stochastic RSI | 8 | Sensitive momentum oscillator |
| Funding Rate | 6 | Are futures traders over-leveraged? |
| Price Acceleration | 12 | Is the selloff speeding up or slowing? |
| Z-Score | 8 | Standard deviations from mean |
| Mean Reversion | 10 | Rubber band distance from average |
| VWAP Deviation | 6 | Are recent buyers winning or losing? |
| Price Percentile | 7 | Where in the 90-day range? |
| Market Structure (highs/lows) | 15 | Quarter-by-quarter structural analysis |
| Buyer Absence | 14 | Low volume during decline = no support |
| RSI Sustained Weakness | 10 | RSI stuck below 50 in downtrend |
| Resistance Rejection | 12 | Multiple touches at same high = topping |

---

## Backtested Rally Entry Signal

The most important indicator. Tested against 90 days of BTC data:

- **Without filters:** 38% win rate (worse than flipping a coin)
- **With strict filters:** 100% win rate (2/2 profitable trades)

**The 7 conditions checked:**
1. Market already turned slightly positive (crash is over)
2. Moderate pullback from 7-day high (-2% to -5%)
3. RSI in "launch zone" (35-55, not extreme)
4. Selling pressure stopped (≤50% red candles recently)
5. Small bounce off recent low (floor confirmed)
6. **BLOCKER:** Larger trend not overextended (<12% rally)
7. **BLOCKER:** Price >4% below high (room to grow)

**Rule:** Only enter when score is ≥75% with NO blockers active.

---

## Data Sources (all free, no API keys required)

| Source | Data |
|---|---|
| [CoinGecko](https://coingecko.com) | BTC price, history, OHLC, global market data, company treasuries |
| [Alternative.me](https://alternative.me/crypto/fear-and-greed-index/) | Crypto Fear & Greed Index |
| [Binance Futures](https://binance.com) | BTC perpetual funding rate |
| [Kraken](https://kraken.com) | Live order book (500 levels) |
| [mempool.space](https://mempool.space) | Bitcoin blockchain transactions |
| [Yahoo Finance](https://finance.yahoo.com) | S&P 500, NASDAQ, VIX, DXY, Gold, Bonds, MSTR (via server proxy) |

---

## Files

```
btc-sentiment/
├── index.html    # Single-page dashboard (all JS/CSS inline)
├── server.py     # Python backend server with /api/macro proxy
└── README.md     # This file
```

---

## Requirements

- Python 3.8+
- No external Python packages required (uses stdlib only)
- Modern browser (Chrome, Firefox, Safari, Edge)

---

## Deployment

### Local (development)

```bash
# Clone the repo
git clone https://github.com/darionruiz-maker/btc-sentiment-tracker.git
cd btc-sentiment-tracker

# Start the server
python3 server.py
```

Open your browser at `http://localhost:8081`

---

### On a VPS / Cloud Server (Ubuntu/Debian)

```bash
# 1. Clone
git clone https://github.com/darionruiz-maker/btc-sentiment-tracker.git
cd btc-sentiment-tracker

# 2. Run the server in the background
nohup python3 server.py > server.log 2>&1 &

# 3. Check it's running
curl http://localhost:8081/api/macro
```

To keep it running after logout, use screen or tmux:

```bash
screen -S btc
python3 server.py
# Press Ctrl+A then D to detach
```

---

### With systemd (auto-restart on reboot)

```bash
# Create service file
sudo nano /etc/systemd/system/btc-dashboard.service
```

Paste:

```ini
[Unit]
Description=BTC Sentiment Dashboard
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/btc-sentiment-tracker
ExecStart=/usr/bin/python3 server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable btc-dashboard
sudo systemctl start btc-dashboard
sudo systemctl status btc-dashboard
```

---

### With Nginx reverse proxy (HTTPS on a domain)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Then get a free SSL cert:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

### On Amazon DevSpaces (current environment)

```bash
cd /home/rudario/.workspace/btc-sentiment-tracker
python3 server.py &
```

Access via: `https://ds-YOURDEVSPACEID--8081.us-east-1.prod.proxy.devspaces.amazon.dev`

---

## How to Use the Dashboard

### Timeframes
- **24H** — intraday signals, good for short-term trades
- **7D** — default, balances noise vs signal
- **30D** — medium-term trend
- **90D** — macro picture

### Reading the Action Signal
- **BUY (green)** — multiple indicators aligned bullish, Rally Entry conditions met
- **HOLD (yellow)** — mixed signals, stay put
- **SELL (red)** — bearish conditions, exit or avoid entry

The confidence % tells you how strongly the indicators agree. 80%+ confidence = high conviction signal.

### The One Rule
> **Only enter a trade when the Rally Entry Signal hits ≥75% with no BLOCKERS.** Anything below that has historically had a worse win rate than a coin flip.

### Time Machine
Toggle the purple **Time Machine** button to see what the dashboard would have predicted 1 week ago — and whether that prediction was correct. Use this to build trust in the signals before trading real money.

---

## Update Intervals

| Data | Refresh Rate |
|---|---|
| Price + indicators | Every 60 seconds |
| Order flow (order book) | Every 30 seconds |
| Whale transactions | Every 5 minutes |
| Macro signals (stocks) | Every 5 minutes |
| Institutional holdings | Every 5 minutes |
| Reversal radar | On each price refresh |

---

## Architecture

```
Browser (index.html)
    │
    ├── CoinGecko API (price, history, fear&greed, global, treasuries)
    ├── Binance Futures API (funding rate)
    ├── Kraken API (order book)
    ├── mempool.space API (whale transactions)
    └── /api/macro ──► server.py ──► Yahoo Finance (7 symbols, parallel)
                       (cached 5 min, threaded, gzip)
```

The server.py acts as a proxy only for Yahoo Finance (which blocks CORS). All other APIs are called directly from the browser.

---

## Disclaimer

This dashboard is for **educational and informational purposes only**. It is not financial advice. Cryptocurrency trading involves significant risk. Always do your own research and never invest more than you can afford to lose. Past performance of backtested signals does not guarantee future results.

---

## License

MIT — free to use, modify, and distribute.
