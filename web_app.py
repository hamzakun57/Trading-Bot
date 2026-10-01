import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.bot import TradingBot
from core.strategies import EnsembleStrategy, SMACrossover, RSIStrategy, MACDStrategy, BollingerStrategy, Signal
from core.ai_model import MLAIStrategy
from core.notifications import notifier

app = FastAPI(title="Trading Bot Dashboard API")

# Setup strategy and Bot
# Setup strategy and Bot
strategy = SMACrossover(2, 4) # Stratégie hyper-réactive pour observer l'interface en action
bot = TradingBot(symbol="BTC/USDT", strategy=strategy, capital=10000, interval_sec=1)
# Mode simulation forcé pour générer de la volatilité et déclencher des trades en boucle:
bot.data.use_binance = False

# Active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send initial full state
        initial_state = {
            "type": "init",
            "candles": bot.data.candles,
            "portfolio": {
                "equity": bot.portfolio.equity,
                "cash": bot.portfolio.cash,
                "stats": bot.portfolio.stats(),
                "positions": [p.to_dict() for p in bot.portfolio.positions.values()],
                "closed_trades": bot.portfolio.closed_trades
            }
        }
        await websocket.send_json(initial_state)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# Background task to produce new candles
async def run_bot_loop():
    print("Starting bot loop background task")
    while True:
        if bot.running:
            print("Bot is running, ticking...")
            # Advance tick
            candle = bot.tick()
            print(f"Candle generated: {candle['close']}")
            
            # Broadcast state
            state = {
                "type": "update",
                "candle": candle,
                "portfolio": {
                    "equity": bot.portfolio.equity,
                    "cash": bot.portfolio.cash,
                    "stats": bot.portfolio.stats(),
                    "positions": [p.to_dict() for p in bot.portfolio.positions.values()],
                    "closed_trades": bot.portfolio.closed_trades
                }
            }
            await manager.broadcast(state)
            print("Broadcasted state")
        await asyncio.sleep(1) # Send update every second in demo mode

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_bot_loop())

@app.get("/")
async def root():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("WebSocket connection attempt...")
    await manager.connect(websocket)
    print("WebSocket connected!")
    try:
        while True:
            data = await websocket.receive_text()
            print("Received ws data:", data)
            # Handle incoming commands from UI
            msg = json.loads(data)
            if msg.get("command") == "start":
                print("Starting bot!")
                bot.running = True
            elif msg.get("command") == "stop":
                print("Stopping bot.")
                bot.running = False
            elif msg.get("command") == "set_strategy":
                val = msg.get("value")
                if val == "aggressive":
                    bot.strategy = SMACrossover(2, 4)
                elif val == "moderate":
                    bot.strategy = SMACrossover(10, 30)
                elif val == "ai":
                    bot.strategy = MLAIStrategy()
                else:
                    bot.strategy = EnsembleStrategy([
                        SMACrossover(10, 30),
                        RSIStrategy(70, 30),
                        MACDStrategy(),
                        BollingerStrategy()
                    ])
                print(f"Strategy changed to: {val}")
            elif msg.get("command") == "manual_trade":
                side = msg.get("side")
                if bot.data.candles:
                    price = bot.data.candles[-1]["close"]
                    if side == "long":
                        bot._execute_signal(Signal.BUY, price)
                    elif side == "short":
                        bot._execute_signal(Signal.SELL, price)
                print(f"Manual override: {side}")
            elif msg.get("command") == "close_position":
                sym = msg.get("symbol")
                if sym in bot.portfolio.positions and bot.data.candles:
                    price = bot.data.candles[-1]["close"]
                    bot.portfolio.close_position(sym, price, "manual-close")
                    print(f"Manual close for {sym}")
            elif msg.get("command") == "update_settings":
                leverage = msg.get("leverage", 10)
                risk = msg.get("risk", 1.0)
                discord_url = msg.get("discord", "")
                
                # Update Risk Manager stats
                # Note: Currently leverage isn't applied to capital strictly, but testing config
                # We'll update the risk_pct directly on the portfolio if available
                # Assuming bot uses a generic risk manager, let's update it if implemented
                if hasattr(bot, "risk_mgr"):
                    bot.risk_mgr.max_risk_pct = risk
                
                # Update Discord Webhook
                if discord_url:
                    notifier.set_discord_webhook(discord_url)
                    
                # Update CCXT Keys
                api_key = msg.get("api_key", "")
                api_secret = msg.get("api_secret", "")
                if api_key and api_secret:
                    from core.exchange import exchange_client
                    exchange_client.initialize(api_key, api_secret, testnet=True)
                
                print(f"Settings updated: Risk {risk}%, Leverage {leverage}x, Webhook {'Set' if discord_url else 'None'}")
            elif msg.get("command") == "run_backtest":
                print("Running backtest from UI...")
                from core.portfolio import Backtester
                bt = Backtester(bot.strategy, capital=10000)
                # On simule un historique massif sur la base des données en mémoire
                prices = [c["close"] for c in bot.data.candles]
                if len(prices) < 50:
                    stats = {"total_trades": 0, "win_rate_%": 0, "total_pnl": 0}
                else:
                    stats = bt.run(prices)
                
                await websocket.send_json({
                    "type": "backtest_result",
                    "stats": stats
                })
    except WebSocketDisconnect:
        print("WebSocket disconnected")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

