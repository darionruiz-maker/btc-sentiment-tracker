#!/usr/bin/env python3
import http.server
import socketserver
import json
import urllib.request
import os
import time
import threading
import gzip
from concurrent.futures import ThreadPoolExecutor, as_completed

PORT = 8081
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

SYMBOLS = {
    '^GSPC': 'S&P 500',
    '^IXIC': 'NASDAQ',
    '^VIX': 'VIX',
    'DX-Y.NYB': 'US Dollar (DXY)',
    'GC=F': 'Gold',
    'TLT': 'US Bonds (20yr)',
    'MSTR': 'MicroStrategy',
}

# Cache with TTL
cache = {}
CACHE_TTL = 300  # 5 minutes

def get_cached(key):
    if key in cache:
        data, ts = cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
    return None

def set_cached(key, data):
    cache[key] = (data, time.time())

def fetch_symbol(sym, name):
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%s?interval=1d&range=30d" % urllib.request.quote(sym)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
        result = data.get('chart', {}).get('result', [{}])[0]
        closes = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
        closes = [c for c in closes if c is not None]
        if closes and len(closes) >= 2:
            price = closes[-1]
            change_1d = ((closes[-1] - closes[-2]) / closes[-2]) * 100
            change_5d = ((closes[-1] - closes[max(0, len(closes)-5)]) / closes[max(0, len(closes)-5)]) * 100
            change_30d = ((closes[-1] - closes[0]) / closes[0]) * 100
            return {
                'symbol': sym,
                'name': name,
                'price': round(price, 2),
                'change_1d': round(change_1d, 2),
                'change_5d': round(change_5d, 2),
                'change_30d': round(change_30d, 2),
                'closes': [round(c, 2) for c in closes[-10:]],
            }
    except Exception as e:
        return {'symbol': sym, 'name': name, 'error': str(e)[:50]}
    return None

def compute_macro_signal(results):
    sp500 = next((r for r in results if r['symbol'] == '^GSPC' and 'price' in r), None)
    vix = next((r for r in results if r['symbol'] == '^VIX' and 'price' in r), None)
    dxy = next((r for r in results if r['symbol'] == 'DX-Y.NYB' and 'price' in r), None)
    gold = next((r for r in results if r['symbol'] == 'GC=F' and 'price' in r), None)
    mstr = next((r for r in results if r['symbol'] == 'MSTR' and 'price' in r), None)

    bearish = 0
    bullish = 0
    reasons = []

    if vix and vix['price'] > 25:
        bearish += 2; reasons.append('VIX elevated (%.0f) = market fear' % vix['price'])
    elif vix and vix['price'] > 20:
        bearish += 1; reasons.append('VIX moderate-high (%.0f)' % vix['price'])
    elif vix and vix['price'] < 14:
        bullish += 1; reasons.append('VIX low (%.0f) = calm market' % vix['price'])

    if sp500 and sp500['change_5d'] < -3:
        bearish += 2; reasons.append('S&P 500 down %.1f%% (5d) = risk-off' % sp500['change_5d'])
    elif sp500 and sp500['change_5d'] < -1:
        bearish += 1; reasons.append('S&P 500 weak (%.1f%% 5d)' % sp500['change_5d'])
    elif sp500 and sp500['change_5d'] > 2:
        bullish += 1; reasons.append('S&P 500 up %.1f%% (5d) = risk-on' % sp500['change_5d'])

    if dxy and dxy['change_5d'] > 1.5:
        bearish += 1; reasons.append('Dollar strengthening (+%.1f%%) = headwind' % dxy['change_5d'])
    elif dxy and dxy['change_5d'] < -1:
        bullish += 1; reasons.append('Dollar weakening (%.1f%%) = tailwind' % dxy['change_5d'])

    if mstr and mstr['change_5d'] < -20:
        bearish += 1; reasons.append('MSTR panic (%.1f%%) = institutional fear' % mstr['change_5d'])

    if gold and gold['change_5d'] > 3:
        reasons.append('Gold rallying (+%.1f%%) = safe haven demand' % gold['change_5d'])

    signal = 'bearish' if bearish >= 3 else 'bullish' if bullish >= 2 else 'neutral'
    verdict = 'RISK-OFF — bad for BTC' if bearish >= 3 else 'RISK-ON — good for BTC' if bullish >= 2 else 'NEUTRAL — not driving BTC either way'

    return signal, verdict, reasons, bearish, bullish


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == '/api/macro':
            self.handle_macro()
        else:
            super().do_GET()

    def handle_macro(self):
        # Check cache first
        cached = get_cached('macro')
        if cached:
            self.send_json(cached)
            return

        # Fetch all symbols in parallel
        results = []
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = {executor.submit(fetch_symbol, sym, name): sym for sym, name in SYMBOLS.items()}
            for future in as_completed(futures, timeout=10):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except:
                    pass

        # Filter out errors for signal computation
        valid = [r for r in results if 'price' in r]
        signal, verdict, reasons, bearish, bullish = compute_macro_signal(valid)

        response = {
            'assets': results,
            'signal': signal,
            'verdict': verdict,
            'reasons': reasons,
            'bearish_count': bearish,
            'bullish_count': bullish,
        }

        set_cached('macro', response)
        self.send_json(response)

    def send_json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'max-age=60')

        # Gzip if client supports it
        accept_enc = self.headers.get('Accept-Encoding', '')
        if 'gzip' in accept_enc and len(body) > 1024:
            body = gzip.compress(body)
            self.send_header('Content-Encoding', 'gzip')

        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        # Add CORS headers to all responses
        if not any(h[0] == 'Access-Control-Allow-Origin' for h in self._headers_buffer if isinstance(h, tuple)):
            pass
        super().end_headers()

    def log_message(self, format, *args):
        pass


class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


if __name__ == '__main__':
    server = ThreadedServer(('', PORT), Handler)
    print("Server running on port %d (threaded, cached)" % PORT)
    server.serve_forever()
