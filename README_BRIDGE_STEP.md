# Market Intelligence AI v1.2 — Exness read-only live quote bridge

This update adds an authenticated endpoint for quotes relayed from the user's Windows MT5 terminal. It does not place trades.

## Important limitations
- Keep the Windows laptop awake, online, and MT5 open/logged in while using the bridge.
- Render's free service may sleep when no requests arrive. This relay sends quotes every 5 seconds while running, but a sleeping service can delay the first update.
- The live Bid/Ask panel is live. The existing indicators, chart candles, SMC estimates, Fibonacci and setup remain based on synthetic demo candles until historical broker candles are integrated separately. Do not trade from those demo-based analysis outputs.
- The in-memory quote cache clears if the Render service restarts.
- Do not share your Exness password or bridge token with anyone. The token is a separate secret used only by this relay.

## Deploy update
1. Upload/replace the updated project files in the GitHub repository from this ZIP, keeping the existing project root layout.
2. In Render, open the service -> Environment -> Add Environment Variable.
3. Add key `BRIDGE_TOKEN` and set a long random secret (at least 32 characters). Save changes and let Render redeploy.
4. Keep the value private. Enter the same value only into the bridge program on your laptop.

## Run the Windows relay
1. Open Command Prompt and run: `python -m pip install MetaTrader5`
2. Keep the Exness MT5 desktop terminal open and logged in.
3. From the extracted project folder run: `python bridge_exness.py`
4. Paste the Render app URL and the `BRIDGE_TOKEN` value when prompted.
5. Leave the Command Prompt window running. Press Ctrl+C to stop.
6. Open the app and select XAUUSD or NATGAS. Live Bid/Ask should appear in the Live Bid/Ask panel.

## Security
The relay sends only broker name, display symbol, broker symbol, Bid, Ask, and tick timestamp. It does not send account number, balance, password, positions, or orders. The endpoint rejects requests without the configured bearer token.
