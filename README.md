# Market Intelligence AI — Mobile PWA

A mobile-first, installable Progressive Web App with a FastAPI analysis backend.

## What works in this build
- Responsive mobile dashboard and PWA manifest/service worker.
- Demo-mode candle feed (synthetic data, clearly labelled).
- Rule-based EMA 20/50/200, RSI, MACD, ATR, ADX approximation, Bollinger Bands and VWAP approximation.
- Fibonacci retracements/extensions.
- Candle pattern candidates, BOS candidates, equal-high/low liquidity estimates, FVG and order-block candidates.
- Confluence score, entry zone, stop, targets and explicit no-trade state.
- CSV OHLCV import and analysis.
- Screenshot upload preview (not AI image interpretation).
- Local-device trading journal.
- Basic EMA-cross historical check (educational; simplified costs/fills).
- Optional read-only MetaTrader 5 bridge on Windows.

## What is NOT yet connected
This package is not a hosted service and does not include a public app URL. It does not yet have:
- A live internet market-data subscription/provider.
- AI vision interpretation for chart screenshots.
- A live economic calendar/news provider.
- Server push notifications.
- A persistent cloud database/user login.
- Broker order execution (intentionally disabled).

A demo feed is not live broker data. Do not trade demo-generated prices.

## Easiest local test
Requires Python 3.10+.
```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```
Open `http://127.0.0.1:8000` on the computer. For a phone on the same Wi-Fi, use `http://COMPUTER-LAN-IP:8000` (viewing works; PWA installation normally requires HTTPS or localhost).

## Publish as a phone-installable PWA
The app needs a public HTTPS address. One route is Render:
1. Create a GitHub account and a new repository.
2. Upload the contents of this project to the repository root.
3. In Render, create a new Blueprint and connect that repository.
4. Render reads `render.yaml` and builds the Dockerfile.
5. When deployment succeeds, open the Render HTTPS URL in Android Chrome.
6. Chrome menu (⋮) → **Install app** or **Add to Home screen**.

The free hosting plan may sleep when idle and is not suitable for a continuous MT5 feed. The hosted web app uses demo mode until a supported live data feed is connected.

## Optional MT5 read-only bridge
The MT5 Python package is Windows-only and requires a running, logged-in MT5 desktop terminal. Run the FastAPI server on that same Windows PC with:
```powershell
$env:MT5_ENABLED="true"
uvicorn server:app --host 0.0.0.0 --port 8000
```
Install the optional package with `pip install MetaTrader5`. Broker symbol names vary: use the exact symbol displayed in MT5 Market Watch. The bridge reads rates only and does not send orders. Do not expose this PC server directly to the public internet; a secure authenticated bridge is needed before remote production use.

## Automated checks
```bash
pip install -r requirements-dev.txt
pytest -q
```

## Risk and research notes
- The confluence score is a rule-based score, not a statistically calibrated win probability.
- Retail OHLC candles cannot reveal exact institutional orders. SMC labels are algorithmic candidates only.
- The current CSV backtest is a simple EMA-cross illustration, not a validation of the full signal rules. It omits variable spread, commissions, slippage, financing and realistic execution.
- No win rate or profitability is guaranteed. Test out-of-sample and on demo first.
