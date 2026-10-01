import logging
from .data import MarketData
from .indicators import Indicators

log = logging.getLogger(__name__)

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
    name = "Ensemble (Vote)"
    def __init__(self, strategies: list):
        self.strategies = strategies

    def generate(self, data: MarketData) -> str:
        votes = {Signal.BUY: 0, Signal.SELL: 0, Signal.HOLD: 0}
        for s in self.strategies:
            votes[s.generate(data)] += 1
        log.debug(f"Votes: {votes}")
        return max(votes, key=votes.get)
