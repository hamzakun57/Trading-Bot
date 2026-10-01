"""
Trading Bot - Concepts de base et mise en œuvre
================================================
Un bot de trading algorithmique avec plusieurs stratégies,
gestion du risque, backtesting et paper trading.
"""

import time
import logging
import json
from datetime import datetime, timedelta
from typing import Optional
import random 

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("trading_bot.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)





class MarketData:
    """Récupère et stocke les données de marché."""

    def __init__(self, symbol: str, max_candles: int = 200):
        self.symbol = symbol
        self.max_candles = max_candles
        self.candles: list[dict] = []

    def fetch_candle(self) -> dict:
        """
        Simule une bougie OHLCV.
        → Remplacer par : ccxt, binance-connector, alpaca, etc.
        """
        prev_close = self.candles[-1]["close"] if self.candles else 100.0
        change = prev_close * random.uniform(-0.015, 0.015)
        open_  = prev_close
        close  = round(open_ + change, 4)
        high   = round(max(open_, close) * random.uniform(1.0, 1.008), 4)
        low    = round(min(open_, close) * random.uniform(0.992, 1.0), 4)
        volume = round(random.uniform(1000, 50000), 2)

        candle = {
            "timestamp": datetime.utcnow().isoformat(),
            "open":   open_,
            "high":   high,
            "low":    low,
            "close":  close,
            "volume": volume,
        }
        self.candles.append(candle)
        if len(self.candles) > self.max_candles:
            self.candles.pop(0)
        return candle

    def closes(self) -> list[float]:
        return [c["close"] for c in self.candles]

    def volumes(self) -> list[float]:
        return [c["volume"] for c in self.candles]




class Indicators:
    """Calcul des indicateurs techniques (sans dépendances externes)."""

    @staticmethod
    def sma(prices: list[float], period: int) -> Optional[float]:
        if len(prices) < period:
            return None
        return round(sum(prices[-period:]) / period, 6)

    @staticmethod
    def ema(prices: list[float], period: int) -> Optional[float]:
        if len(prices) < period:
            return None
        k = 2 / (period + 1)
        ema_val = sum(prices[:period]) / period
        for price in prices[period:]:
            ema_val = price * k + ema_val * (1 - k)
        return round(ema_val, 6)

    @staticmethod
    def rsi(prices: list[float], period: int = 14) -> Optional[float]:
        if len(prices) < period + 1:
            return None
        gains, losses = [], []
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i - 1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return round(100 - 100 / (1 + rs), 2)

    @staticmethod
    def macd(prices: list[float], fast=12, slow=26, signal=9
             ) -> Optional[tuple[float, float, float]]:
        if len(prices) < slow + signal:
            return None
        ema_fast = Indicators.ema(prices, fast)
        ema_slow = Indicators.ema(prices, slow)
        if ema_fast is None or ema_slow is None:
            return None
        macd_line = ema_fast - ema_slow
        
        macd_vals = []
        for i in range(signal, 0, -1):
            pf = Indicators.ema(prices[:-i] if i > 0 else prices, fast)
            ps = Indicators.ema(prices[:-i] if i > 0 else prices, slow)
            if pf and ps:
                macd_vals.append(pf - ps)
        if not macd_vals:
            return None
        sig = sum(macd_vals[-signal:]) / min(len(macd_vals), signal)
        histogram = macd_line - sig
        return round(macd_line, 6), round(sig, 6), round(histogram, 6)

    @staticmethod
    def bollinger_bands(prices: list[float], period=20, k=2.0
                        ) -> Optional[tuple[float, float, float]]:
        if len(prices) < period:
            return None
        window = prices[-period:]
        mid = sum(window) / period
        std = (sum((x - mid) ** 2 for x in window) / period) ** 0.5
        return round(mid - k * std, 4), round(mid, 4), round(mid + k * std, 4)

    @staticmethod
    def atr(candles: list[dict], period=14) -> Optional[float]:
        if len(candles) < period + 1:
            return None
        trs = []
        for i in range(1, len(candles)):
            h, l, pc = candles[i]["high"], candles[i]["low"], candles[i-1]["close"]
            trs.append(max(h - l, abs(h - pc), abs(l - pc)))
        return round(sum(trs[-period:]) / period, 4)




class Signal:
    BUY  = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Strategy:
    """Classe de base pour toutes les stratégies."""
    name = "Base"

    def generate(self, data: MarketData) -> str:
        raise NotImplementedError


class SMACrossover(Strategy):
    """Croisement de deux moyennes mobiles simples."""
    name = "SMA Crossover"

    def __init__(self, fast=10, slow=30):
        self.fast, self.slow = fast, slow

    def generate(self, data: MarketData) -> str:
        closes = data.closes()
        sma_f = Indicators.sma(closes, self.fast)
        sma_s = Indicators.sma(closes, self.slow)
        if not sma_f or not sma_s:
            return Signal.HOLD

        prev_closes = closes[:-1]
        prev_f = Indicators.sma(prev_closes, self.fast)
        prev_s = Indicators.sma(prev_closes, self.slow)

        if prev_f and prev_s:
            if prev_f <= prev_s and sma_f > sma_s:
                return Signal.BUY   
            if prev_f >= prev_s and sma_f < sma_s:
                return Signal.SELL 
        return Signal.HOLD


class RSIStrategy(Strategy):
    """Stratégie basée sur le RSI (sur-achat / sur-vente)."""
    name = "RSI Mean Reversion"

    def __init__(self, overbought=70, oversold=30, period=14):
        self.overbought = overbought
        self.oversold   = oversold
        self.period     = period

    def generate(self, data: MarketData) -> str:
        rsi = Indicators.rsi(data.closes(), self.period)
        if rsi is None:
            return Signal.HOLD
        if rsi < self.oversold:
            return Signal.BUY
        if rsi > self.overbought:
            return Signal.SELL
        return Signal.HOLD


class MACDStrategy(Strategy):
    """Croisement MACD / Signal."""
    name = "MACD Crossover"

    def generate(self, data: MarketData) -> str:
        closes = data.closes()
        result = Indicators.macd(closes)
        if not result:
            return Signal.HOLD
        macd_line, sig_line, hist = result
        prev_result = Indicators.macd(closes[:-1])
        if not prev_result:
            return Signal.HOLD
        prev_hist = prev_result[2]

        if prev_hist < 0 and hist > 0:
            return Signal.BUY
        if prev_hist > 0 and hist < 0:
            return Signal.SELL
        return Signal.HOLD


class BollingerStrategy(Strategy):
    """Retour à la moyenne avec les bandes de Bollinger."""
    name = "Bollinger Bands"

    def generate(self, data: MarketData) -> str:
        closes = data.closes()
        result = Indicators.bollinger_bands(closes)
        if not result:
            return Signal.HOLD
        lower, mid, upper = result
        price = closes[-1]
        if price < lower:
            return Signal.BUY
        if price > upper:
            return Signal.SELL
        return Signal.HOLD


class EnsembleStrategy(Strategy):
    """Combine plusieurs stratégies par vote majoritaire."""
    name = "Ensemble (Vote)"

    def __init__(self, strategies: list):
        self.strategies = strategies

    def generate(self, data: MarketData) -> str:
        votes = {Signal.BUY: 0, Signal.SELL: 0, Signal.HOLD: 0}
        for s in self.strategies:
            votes[s.generate(data)] += 1
        log.debug(f"Votes: {votes}")
        return max(votes, key=votes.get)




class RiskManager:
    """
    Calcule la taille des positions et applique les règles de risque.
    Règle de base : ne jamais risquer plus de X% du capital par trade.
    """

    def __init__(self, max_risk_pct=1.0, max_drawdown_pct=10.0):
        self.max_risk_pct      = max_risk_pct      
        self.max_drawdown_pct  = max_drawdown_pct  
        self.peak_equity       = None

    def position_size(self, capital: float, entry: float,
                      stop_loss: float) -> float:
        """Kelly / Fixed Fraction simplifié."""
        risk_amount = capital * (self.max_risk_pct / 100)
        distance    = abs(entry - stop_loss)
        if distance == 0:
            return 0.0
        qty = risk_amount / distance
        max_qty = capital / entry  
        return round(min(qty, max_qty), 6)

    def stop_loss(self, entry: float, atr: float,
                  side: str = "long", multiplier=2.0) -> float:
        """Stop-loss dynamique basé sur l'ATR."""
        if side == "long":
            return round(entry - multiplier * atr, 4)
        return round(entry + multiplier * atr, 4)

    def take_profit(self, entry: float, stop: float,
                    rr_ratio=2.0) -> float:
        """Take-profit avec un ratio Risk/Reward donné."""
        distance = abs(entry - stop)
        if entry > stop:  # long
            return round(entry + rr_ratio * distance, 4)
        return round(entry - rr_ratio * distance, 4)

    def check_drawdown(self, equity: float) -> bool:
        """Retourne True si le drawdown est acceptable."""
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
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.pnl       = 0.0

    def update_pnl(self, current_price: float):
        if self.side == "long":
            self.pnl = (current_price - self.entry) * self.qty
        else:
            self.pnl = (self.entry - current_price) * self.qty
        return self.pnl

    def __repr__(self):
        return (f"Position({self.symbol} {self.side} "
                f"qty={self.qty} entry={self.entry} pnl={self.pnl:.2f})")


class Portfolio:
    """Gestion du portefeuille en paper trading."""

    def __init__(self, initial_capital: float = 10_000):
        self.cash              = initial_capital
        self.initial_capital   = initial_capital
        self.positions: dict[str, Position] = {}
        self.closed_trades: list[dict]      = []

    @property
    def equity(self):
        return self.cash + sum(p.pnl for p in self.positions.values())

    @property
    def total_pnl(self):
        return self.equity - self.initial_capital

    def open_position(self, pos: Position) -> bool:
        cost = pos.entry * pos.qty
        if cost > self.cash:
            log.warning(f"❌ Capital insuffisant: besoin {cost:.2f}, disponible {self.cash:.2f}")
            return False
        self.cash -= cost
        self.positions[pos.symbol] = pos
        log.info(f"📈 OUVERTURE | {pos.symbol} {pos.side} "
                 f"qty={pos.qty} @ {pos.entry} | SL={pos.stop} TP={pos.tp}")
        return True

    def close_position(self, symbol: str, price: float, reason: str = "signal"):
        pos = self.positions.pop(symbol, None)
        if not pos:
            return
        proceeds = price * pos.qty
        self.cash += proceeds
        pnl = pos.update_pnl(price)
        self.cash += pnl  
        record = {
            "symbol":    symbol,
            "side":      pos.side,
            "qty":       pos.qty,
            "entry":     pos.entry,
            "exit":      price,
            "pnl":       round(pnl, 2),
            "reason":    reason,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.closed_trades.append(record)
        emoji = "✅" if pnl >= 0 else "❌"
        log.info(f"{emoji} FERMETURE | {symbol} @ {price} | "
                 f"PnL={pnl:+.2f} ({reason})")

    def stats(self) -> dict:
        if not self.closed_trades:
            return {}
        pnls    = [t["pnl"] for t in self.closed_trades]
        wins    = [p for p in pnls if p > 0]
        losses  = [p for p in pnls if p <= 0]
        win_rate = len(wins) / len(pnls) * 100 if pnls else 0
        avg_win  = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        profit_factor = abs(sum(wins) / sum(losses)) if sum(losses) != 0 else float("inf")
        return {
            "total_trades":    len(pnls),
            "win_rate_%":      round(win_rate, 1),
            "total_pnl":       round(sum(pnls), 2),
            "avg_win":         round(avg_win, 2),
            "avg_loss":        round(avg_loss, 2),
            "profit_factor":   round(profit_factor, 2),
            "max_single_loss": round(min(pnls), 2) if pnls else 0,
            "equity":          round(self.equity, 2),
        }




class Backtester:
    """
    Simule une stratégie sur données historiques.
    Usage simple : charger une liste de prix et rejouer.
    """

    def __init__(self, strategy: Strategy, capital=10_000,
                 atr_multiplier=2.0, rr_ratio=2.0):
        self.strategy      = strategy
        self.capital       = capital
        self.atr_mult      = atr_multiplier
        self.rr            = rr_ratio

    def run(self, prices: list[float]) -> dict:
        """
        prices : liste de prix de clôture.
        Retourne les statistiques du backtest.
        """
        portfolio = Portfolio(self.capital)
        risk_mgr  = RiskManager()
        data      = MarketData("BT")

        for price in prices:
            
            candle = {
                "timestamp": datetime.utcnow().isoformat(),
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
                    portfolio.open_position(
                        Position("BT", "long", qty, price, stop, tp))

            elif signal == Signal.SELL and "BT" in portfolio.positions:
                portfolio.close_position("BT", price, "signal")

        
        if "BT" in portfolio.positions and prices:
            portfolio.close_position("BT", prices[-1], "end-of-backtest")

        return portfolio.stats()




class TradingBot:
    """
    Boucle principale du bot de trading.
    Mode : Paper Trading (simulation en temps réel).
    """

    def __init__(self, symbol: str, strategy: Strategy,
                 capital: float = 10_000, interval_sec: int = 5):
        self.symbol       = symbol
        self.strategy     = strategy
        self.interval     = interval_sec
        self.data         = MarketData(symbol)
        self.portfolio    = Portfolio(capital)
        self.risk_mgr     = RiskManager(max_risk_pct=1.0, max_drawdown_pct=15.0)
        self.running      = False
        self.iteration    = 0

    def _execute_signal(self, signal: str, price: float):
        atr = Indicators.atr(self.data.candles)
        if atr is None:
            atr = price * 0.01

        if signal == Signal.BUY and self.symbol not in self.portfolio.positions:
            stop = self.risk_mgr.stop_loss(price, atr, "long")
            tp   = self.risk_mgr.take_profit(price, stop)
            qty  = self.risk_mgr.position_size(self.portfolio.equity, price, stop)
            if qty > 0:
                self.portfolio.open_position(
                    Position(self.symbol, "long", qty, price, stop, tp))

        elif signal == Signal.SELL:
            if self.symbol in self.portfolio.positions:
                self.portfolio.close_position(self.symbol, price, "signal")

    def _check_exits(self, price: float):
        pos = self.portfolio.positions.get(self.symbol)
        if not pos:
            return
        pos.update_pnl(price)
        if pos.side == "long":
            if price <= pos.stop:
                self.portfolio.close_position(self.symbol, price, "stop-loss")
            elif price >= pos.tp:
                self.portfolio.close_position(self.symbol, price, "take-profit")

    def run(self, max_iterations: int = 100):
        """Boucle principale du bot."""
        self.running = True
        log.info(f"🤖 Bot démarré | {self.symbol} | Stratégie: {self.strategy.name}")
        log.info(f"   Capital: {self.portfolio.cash:.2f} | Intervalle: {self.interval}s")

        while self.running and self.iteration < max_iterations:
            try:
                candle = self.data.fetch_candle()
                price  = candle["close"]
                self.iteration += 1

                # Vérifier drawdown
                if not self.risk_mgr.check_drawdown(self.portfolio.equity):
                    log.error("🛑 Bot arrêté : drawdown maximum atteint")
                    break

                
                self._check_exits(price)

                
                if len(self.data.candles) >= 35:
                    signal = self.strategy.generate(self.data)
                    rsi    = Indicators.rsi(self.data.closes())
                    sma20  = Indicators.sma(self.data.closes(), 20)

                    if self.iteration % 10 == 0:
                        in_pos = self.symbol in self.portfolio.positions
                        log.info(
                            f"[{self.iteration:03d}] {self.symbol} "
                            f"Price={price:.4f} | Signal={signal} | "
                            f"RSI={rsi:.1f if rsi else '—'} | "
                            f"SMA20={sma20:.4f if sma20 else '—'} | "
                            f"Equity={self.portfolio.equity:.2f} | "
                            f"Position={'Oui' if in_pos else 'Non'}"
                        )

                    if signal != Signal.HOLD:
                        self._execute_signal(signal, price)

                time.sleep(self.interval)

            except KeyboardInterrupt:
                log.info("⏹️  Interruption utilisateur")
                break
            except Exception as e:
                log.error(f"Erreur: {e}")
                break

        
        if self.symbol in self.portfolio.positions:
            last_price = self.data.closes()[-1]
            self.portfolio.close_position(self.symbol, last_price, "bot-stop")

        self.running = False
        stats = self.portfolio.stats()
        log.info("═" * 60)
        log.info("📊 RÉSULTATS FINAUX")
        for k, v in stats.items():
            log.info(f"   {k:22s}: {v}")
        log.info("═" * 60)
        return stats




if __name__ == "__main__":
    print("\n" + "═"*60)
    print("  🤖 TRADING BOT - Démonstration")
    print("═"*60)

    
    print("\n[1] Backtest sur 500 bougies simulées...")
    prices = [100.0]
    for _ in range(499):
        prices.append(round(prices[-1] * (1 + random.uniform(-0.012, 0.012)), 4))

    strategy = EnsembleStrategy([
        SMACrossover(10, 30),
        RSIStrategy(70, 30),
        MACDStrategy(),
        BollingerStrategy(),
    ])

    bt = Backtester(strategy, capital=10_000)
    bt_stats = bt.run(prices)
    print(f"   Résultat backtest : {bt_stats}")

   
    print("\n[2] Paper Trading (50 itérations, intervalle=0s)...")
    bot = TradingBot(
        symbol="BTC/USDT",
        strategy=strategy,
        capital=10_000,
        interval_sec=0  
    )
    bot.run(max_iterations=50)
