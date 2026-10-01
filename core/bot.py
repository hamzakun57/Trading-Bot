import time
import logging
from .data import MarketData
from .indicators import Indicators
from .strategies import Strategy, Signal
from .portfolio import Portfolio, RiskManager, Position

log = logging.getLogger(__name__)

class TradingBot:
    def __init__(self, symbol: str, strategy: Strategy, capital: float = 10_000, interval_sec: int = 5):
        self.symbol       = symbol
        self.strategy     = strategy
        self.interval     = interval_sec
        self.data         = MarketData(symbol)
        self.portfolio    = Portfolio(capital)
        self.risk_mgr     = RiskManager(max_risk_pct=1.0, max_drawdown_pct=99.0) 
        self.running      = False
        self.iteration    = 0
        self.on_candle_cb = None    
        self.on_trade_cb  = None    

       
        if hasattr(self.data, 'load_historical'):
            self.data.load_historical(100)
            self.iteration += len(self.data.candles)
        else:
            for _ in range(100):
                self.data.fetch_candle()
                self.iteration += 1

    def set_callbacks(self, on_candle=None, on_trade=None):
        self.on_candle_cb = on_candle
        self.on_trade_cb = on_trade

    def _execute_signal(self, signal: str, price: float):
        atr = Indicators.atr(self.data.candles)
        if atr is None:
            atr = price * 0.01

        if signal == Signal.BUY and self.symbol not in self.portfolio.positions:
            stop = self.risk_mgr.stop_loss(price, atr, "long")
            tp   = self.risk_mgr.take_profit(price, stop)
            qty  = self.risk_mgr.position_size(self.portfolio.equity, price, stop)
            if qty > 0:
                pos = Position(self.symbol, "long", qty, price, stop, tp)
                self.portfolio.open_position(pos)
                if self.on_trade_cb: self.on_trade_cb("open", pos.to_dict())

        elif signal == Signal.SELL:
            if self.symbol in self.portfolio.positions:
                self.portfolio.close_position(self.symbol, price, "signal")
                if self.on_trade_cb: self.on_trade_cb("close", {"symbol": self.symbol, "price": price})

    def _check_exits(self, price: float):
        pos = self.portfolio.positions.get(self.symbol)
        if not pos: return
        pos.update_pnl(price)
        if pos.side == "long":
            if price <= pos.stop:
                self.portfolio.close_position(self.symbol, price, "stop-loss")
                if self.on_trade_cb: self.on_trade_cb("close", {"symbol": self.symbol, "price": price})
            elif price >= pos.tp:
                self.portfolio.close_position(self.symbol, price, "take-profit")
                if self.on_trade_cb: self.on_trade_cb("close", {"symbol": self.symbol, "price": price})

    def tick(self) -> dict:
        """Advance one tick (for webloop). Returns the candle."""
        candle = self.data.fetch_candle()
        price  = candle["close"]
        self.iteration += 1

        if not self.risk_mgr.check_drawdown(self.portfolio.equity):
            self.running = False
            return candle

        self._check_exits(price)

        if len(self.data.candles) >= 35:
            signal = self.strategy.generate(self.data)
            if signal != Signal.HOLD:
                self._execute_signal(signal, price)
                
        if self.on_candle_cb:
            state = {
                "candle": candle,
                "portfolio": {
                    "equity": self.portfolio.equity,
                    "cash": self.portfolio.cash,
                    "stats": self.portfolio.stats(),
                    "positions": [p.to_dict() for p in self.portfolio.positions.values()]
                }
            }
            self.on_candle_cb(state)
            
        return candle

    def run(self, max_iterations: int = 100):
        self.running = True
        log.info(f"🤖 Bot démarré | {self.symbol}")
        while self.running and self.iteration < max_iterations:
            self.tick()
            time.sleep(self.interval)
            
        if self.symbol in self.portfolio.positions:
            last_price = self.data.closes()[-1]
            self.portfolio.close_position(self.symbol, last_price, "bot-stop")
        self.running = False
        return self.portfolio.stats()
