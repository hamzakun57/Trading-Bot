from typing import Optional

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
    def macd(prices: list[float], fast=12, slow=26, signal=9) -> Optional[tuple[float, float, float]]:
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
    def bollinger_bands(prices: list[float], period=20, k=2.0) -> Optional[tuple[float, float, float]]:
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
