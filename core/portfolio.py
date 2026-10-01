import logging
from datetime import datetime
from .data import MarketData
from .indicators import Indicators
from .strategies import Strategy, Signal
from .notifications import notifier
from .exchange import exchange_client

log = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, max_risk_pct=1.0, max_drawdown_pct=10.0):
        self.max_risk_pct      = max_risk_pct
        self.max_drawdown_pct  = max_drawdown_pct
        self.peak_equity       = None

    def position_size(self, capital: float, entry: float, stop_loss: float) -> float:
        risk_amount = capital * (self.max_risk_pct / 100)
        distance    = abs(entry - stop_loss)
        if distance == 0:
            return 0.0
        qty = risk_amount / distance
        max_qty = capital / entry
        target_qty = min(qty, max_qty)
        return int(target_qty * 1000000) / 1000000.0

    def stop_loss(self, entry: float, atr: float, side: str = "long", multiplier=2.0) -> float:
        if side == "long":
            return round(entry - multiplier * atr, 4)
        return round(entry + multiplier * atr, 4)

    def take_profit(self, entry: float, stop: float, rr_ratio=2.0) -> float:
        distance = abs(entry - stop)
        if entry > stop:
            return round(entry + rr_ratio * distance, 4)
        return round(entry - rr_ratio * distance, 4)

    def check_drawdown(self, equity: float) -> bool:
        if self.peak_equity is None or equity > self.peak_equity:
            self.peak_equity = equity
        dd_pct = (self.peak_equity - equity) / self.peak_equity * 100
        if dd_pct >= self.max_drawdown_pct:
            log.warning(f"⚠️  Max drawdown atteint : {dd_pct:.1f}%")
            return False
        return True

class Position:
    def __init__(self, symbol, side, qty, entry, stop, tp, timestamp=None):
        self.symbol    = symbol
        self.side      = side
        self.qty       = qty
        self.entry     = entry
        self.stop      = stop
        self.tp        = tp
        self.timestamp = timestamp or (datetime.utcnow().isoformat() + "Z")
        self.pnl       = 0.0

    def update_pnl(self, current_price: float):
        if self.side == "long":
            self.pnl = (current_price - self.entry) * self.qty
        else:
            self.pnl = (self.entry - current_price) * self.qty
        return self.pnl

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "side": self.side,
            "qty": self.qty,
            "entry": self.entry,
            "stop": self.stop,
            "tp": self.tp,
            "pnl": self.pnl,
            "timestamp": self.timestamp
        }

class Portfolio:
    def __init__(self, initial_capital: float = 10_000):
        self.cash              = initial_capital
        self.initial_capital   = initial_capital
        self.positions         = {}
        self.closed_trades     = []

    @property
    def equity(self):
        return self.cash + sum((p.entry * p.qty) + p.pnl for p in self.positions.values())

    def open_position(self, pos: Position) -> bool:
        cost = pos.entry * pos.qty
        if cost > self.cash + 1e-6:
            log.warning(f"❌ Capital insuffisant: besoin {cost:.2f}, disponible {self.cash:.2f}")
            return False
        self.cash -= cost
        self.positions[pos.symbol] = pos
        log.info(f"📈 OUVERTURE | {pos.symbol} {pos.side} qty={pos.qty} @ {pos.entry} | SL={pos.stop} TP={pos.tp}")
        
        # Alerte Discord
        emoji = "🟢" if pos.side == "long" else "🔴"
        notifier.send_discord_message(
            f"{emoji} **NOUVELLE POSITION {pos.side.upper()}**\nPaire: {pos.symbol}\nPrix d'entrée: ${pos.entry}\nQuantité: {pos.qty:.4f}\nSL: ${pos.stop} | TP: ${pos.tp}",
            color=0x00E676 if pos.side == "long" else 0xFF1744
        )
        
   
        ccxt_side = "buy" if pos.side == "long" else "sell"
        exchange_client.create_market_order(pos.symbol, ccxt_side, pos.qty)
        
        return True

    def close_position(self, symbol: str, price: float, reason: str = "signal"):
        pos = self.positions.pop(symbol, None)
        if not pos:
            return
        proceeds = price * pos.qty
        self.cash += proceeds
        pnl = pos.update_pnl(price)
        record = {
            "symbol":    symbol,
            "side":      pos.side,
            "qty":       pos.qty,
            "entry":     pos.entry,
            "exit":      price,
            "pnl":       round(pnl, 2),
            "reason":    reason,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self.closed_trades.append(record)
        emoji = "✅" if pnl >= 0 else "❌"
        msg = f"{emoji} FERMETURE | {symbol} @ {price} | PnL={pnl:+.2f} ({reason})"
        log.info(msg)
        
        # Alerte Discord
        notifier.send_discord_message(
            f"**POSITION FERMÉE**\nPaire: {symbol}\nPrix de sortie: ${price}\nRaison: {reason}\n**PnL: {pnl:+.2f}$ {emoji}**",
            color=0x00E676 if pnl >= 0 else 0xFF1744
        )
        
        
        ccxt_side = "sell" if pos.side == "long" else "buy"
        exchange_client.create_market_order(symbol, ccxt_side, pos.qty)

    def stats(self) -> dict:
        if not self.closed_trades:
            return {}
        pnls    = [t["pnl"] for t in self.closed_trades]
        wins    = [p for p in pnls if p > 0]
        losses  = [p for p in pnls if p <= 0]
        win_rate = len(wins) / len(pnls) * 100 if pnls else 0
        profit_factor = abs(sum(wins) / sum(losses)) if sum(losses) != 0 else "inf"
        return {
            "total_trades": len(pnls),
            "win_rate_%": round(win_rate, 1),
            "total_pnl": round(sum(pnls), 2),
            "profit_factor": round(profit_factor, 2) if isinstance(profit_factor, (int, float)) else profit_factor,
            "equity": round(self.equity, 2),
        }

class Backtester:
    def __init__(self, strategy: Strategy, capital=10_000, atr_multiplier=2.0, rr_ratio=2.0):
        self.strategy      = strategy
        self.capital       = capital
        self.atr_mult      = atr_multiplier
        self.rr            = rr_ratio

    def run(self, prices: list[float]) -> dict:
        portfolio = Portfolio(self.capital)
        risk_mgr  = RiskManager()
        data      = MarketData("BT")

        for price in prices:
            candle = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "open": price, "high": price * 1.002,
                "low": price * 0.998, "close": price, "volume": 1000
            }
            data.candles.append(candle)

            if "BT" in portfolio.positions:
                pos = portfolio.positions["BT"]
                pos.update_pnl(price)
                if pos.side == "long":
                    if price <= pos.stop:
                        portfolio.close_position("BT", price, "stop-loss")
                        continue
                    if price >= pos.tp:
                        portfolio.close_position("BT", price, "take-profit")
                        continue

            if len(data.candles) < 35:
                continue

            signal = self.strategy.generate(data)
            atr = Indicators.atr(data.candles) or price * 0.01

            if signal == Signal.BUY and "BT" not in portfolio.positions:
                stop = risk_mgr.stop_loss(price, atr, "long", self.atr_mult)
                tp   = risk_mgr.take_profit(price, stop, self.rr)
                qty  = risk_mgr.position_size(portfolio.equity, price, stop)
                if qty > 0:
                    portfolio.open_position(Position("BT", "long", qty, price, stop, tp))
            elif signal == Signal.SELL and "BT" in portfolio.positions:
                portfolio.close_position("BT", price, "signal")

        if "BT" in portfolio.positions and prices:
            portfolio.close_position("BT", prices[-1], "end-of-backtest")
        return portfolio.stats()
