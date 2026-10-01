import random
import json
import urllib.request
from datetime import datetime

class MarketData:
    def __init__(self, symbol: str, max_candles: int = 200, use_binance: bool = True):
        self.symbol_raw = symbol
        self.symbol = symbol.replace("/", "").upper() 
        self.max_candles = max_candles
        self.candles = []
        self.use_binance = use_binance
        self.first_candle_time = datetime.utcnow()

    def _fetch_from_api(self, limit=1) -> list:
    
        url = f"https://api.bybit.com/v5/market/kline?category=spot&symbol={self.symbol}&interval=1&limit={limit}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                payload = json.loads(response.read().decode('utf-8'))
                
            if payload.get("retCode") != 0:
                print(f"Erreur API Bybit: {payload.get('retMsg')}")
                return []
                
            klines = payload["result"]["list"]
            
            klines.reverse()
            
            formatted = []
            for kline in klines:
                open_time = int(kline[0])
                formatted.append({
                    "timestamp": datetime.utcfromtimestamp(open_time / 1000).isoformat() + "Z",
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5]),
                })
            return formatted
        except Exception as e:
            print(f"Erreur API de marché: {e}")
            return []

    def load_historical(self, limit=100):
        if self.use_binance:  
            
            hist = self._fetch_from_api(limit=limit)
            if hist:
                self.candles.extend(hist)
                return
                
        
        for _ in range(limit):
            self.fetch_candle()

    def fetch_candle(self) -> dict:
        """Récupère la bougie live (ou simule)."""
        if self.use_binance:
            latest = self._fetch_from_api(limit=1)
            if latest:
                candle = latest[0]
                
                if self.candles and candle["timestamp"] == self.candles[-1]["timestamp"]:
                    ms_time = datetime.utcnow()
                    candle["timestamp"] = ms_time.isoformat() + "Z"
                    
                self.candles.append(candle)
                if len(self.candles) > self.max_candles:
                    self.candles.pop(0)
                return candle

       
        self.first_candle_time = self.first_candle_time + __import__('datetime').timedelta(seconds=1)
        prev_close = self.candles[-1]["close"] if self.candles else 100.0
        change = prev_close * random.uniform(-0.015, 0.015)
        open_  = prev_close
        close  = round(open_ + change, 4)
        high   = round(max(open_, close) * random.uniform(1.0, 1.008), 4)
        low    = round(min(open_, close) * random.uniform(0.992, 1.0), 4)
        volume = round(random.uniform(1000, 50000), 2)

        candle = {
            "timestamp": self.first_candle_time.isoformat() + "Z",
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
