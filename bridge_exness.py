"""Read-only Exness MT5 quote relay for Market Intelligence AI.
Requires Windows, an open/logged-in MT5 desktop terminal, and the MetaTrader5 package.
Never places, modifies, or closes orders.
"""
import json, time, urllib.request, urllib.error
import MetaTrader5 as mt5

APP_URL = input('Paste your Render app URL (https://....onrender.com): ').strip().rstrip('/')
TOKEN = input('Paste the BRIDGE_TOKEN configured in Render: ').strip()
if not APP_URL.startswith('https://') or not TOKEN:
    raise SystemExit('A valid HTTPS app URL and bridge token are required.')

# Confirmed symbol names from the user's Exness terminal.
SYMBOLS = {'XAUUSD': 'XAUUSD', 'NATGAS': 'XNGUSDm'}

if not mt5.initialize():
    raise SystemExit(f'Could not connect to MT5: {mt5.last_error()}. Open MT5 and log in first.')
print('Connected to MT5. Sending read-only quotes. Press Ctrl+C to stop.')

def send(payload):
    data=json.dumps(payload).encode('utf-8')
    req=urllib.request.Request(APP_URL+'/api/bridge/quotes', data=data,
        headers={'Content-Type':'application/json','Authorization':'Bearer '+TOKEN}, method='POST')
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.read().decode('utf-8')

try:
    while True:
        for app_symbol, broker_symbol in SYMBOLS.items():
            if not mt5.symbol_select(broker_symbol, True):
                print(f'{broker_symbol}: cannot select symbol - {mt5.last_error()}')
                continue
            tick=mt5.symbol_info_tick(broker_symbol)
            if tick is None or tick.bid <= 0 or tick.ask <= 0:
                print(f'{broker_symbol}: no valid quote yet')
                continue
            payload={'broker':'Exness','symbol':app_symbol,'broker_symbol':broker_symbol,
                     'bid':tick.bid,'ask':tick.ask,'time':int(tick.time)}
            try:
                print(send(payload))
                print(f'{app_symbol} Bid={tick.bid} Ask={tick.ask}')
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
                print(f'Upload failed for {app_symbol}: {exc}')
        time.sleep(5)
except KeyboardInterrupt:
    print('Stopping quote relay...')
finally:
    mt5.shutdown()
