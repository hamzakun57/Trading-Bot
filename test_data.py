from core.data import MarketData
print("Testing MarketData...")
try:
    md = MarketData("BTC/USDT")
    md.load_historical(limit=10)
    print(f"Loaded {len(md.candles)} candles")
    if md.candles:
        print("First candle:", md.candles[0])
except Exception as e:
    import traceback
    traceback.print_exc()
