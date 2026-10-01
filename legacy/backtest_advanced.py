"""
backtest_advanced.py
────────────────────
Backtest avancé : comparaison de stratégies, courbe d'équité,
Sharpe ratio, maximum drawdown, rapport CSV.
"""

import csv
import math
import random
from datetime import datetime, timedelta

from bot import (
    MarketData, Indicators, Signal,
    SMACrossover, RSIStrategy, MACDStrategy,
    BollingerStrategy, EnsembleStrategy,
    Portfolio, Position, RiskManager
)



def generate_price_series(n=1000, seed=42, trend=0.0002, volatility=0.012):
    random.seed(seed)
    prices = [100.0]
    for _ in range(n - 1):
        daily_return = random.gauss(trend, volatility)
        prices.append(round(prices[-1] * (1 + daily_return), 4))
    return prices



def sharpe_ratio(returns: list[float], risk_free=0.0, annualize=252) -> float:
    if len(returns) < 2:
        return 0.0
    mean_r = sum(returns) / len(returns)
    std_r  = math.sqrt(sum((r - mean_r) ** 2 for r in returns) / len(returns))
    if std_r == 0:
        return 0.0
    return round((mean_r - risk_free) * math.sqrt(annualize) / std_r, 3)


def max_drawdown(equity_curve: list[float]) -> float:
    peak = equity_curve[0]
    max_dd = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)


def calmar_ratio(total_return_pct: float, max_dd: float) -> float:
    return round(total_return_pct / max_dd, 3) if max_dd != 0 else 0.0


def full_backtest(strategy, prices: list[float], capital=10_000,
                  atr_mult=2.0, rr=2.0) -> dict:
    portfolio   = Portfolio(capital)
    risk_mgr    = RiskManager()
    data        = MarketData("BT")
    equity_curve = [capital]
    trade_returns = []

    for price in prices:
        candle = {
            "timestamp": datetime.utcnow().isoformat(),
            "open": price, "high": price * 1.002,
            "low": price * 0.998, "close": price, "volume": 1000,
        }
        data.candles.append(candle)

        # Stop / TP
        if "BT" in portfolio.positions:
            pos = portfolio.positions["BT"]
            pos.update_pnl(price)
            if pos.side == "long":
                if price <= pos.stop:
                    portfolio.close_position("BT", price, "stop-loss")
                    equity_curve.append(portfolio.equity)
                    continue
                if price >= pos.tp:
                    portfolio.close_position("BT", price, "take-profit")
                    equity_curve.append(portfolio.equity)
                    continue

        if len(data.candles) < 40:
            equity_curve.append(portfolio.equity)
            continue

        signal = strategy.generate(data)
        atr    = Indicators.atr(data.candles) or price * 0.01

        if signal == Signal.BUY and "BT" not in portfolio.positions:
            stop = risk_mgr.stop_loss(price, atr, "long", atr_mult)
            tp   = risk_mgr.take_profit(price, stop, rr)
            qty  = risk_mgr.position_size(portfolio.equity, price, stop)
            if qty > 0:
                portfolio.open_position(
                    Position("BT", "long", qty, price, stop, tp))

        elif signal == Signal.SELL and "BT" in portfolio.positions:
            portfolio.close_position("BT", price, "signal")

        equity_curve.append(portfolio.equity)

    
    if "BT" in portfolio.positions and prices:
        portfolio.close_position("BT", prices[-1], "end")

    stats = portfolio.stats()
    if not stats:
        return {"error": "Pas assez de trades"}

    pnls    = [t["pnl"] for t in portfolio.closed_trades]
    ret_pct = (portfolio.equity - capital) / capital * 100
    pct_returns = [p / capital for p in pnls]

    return {
        **stats,
        "return_%":         round(ret_pct, 2),
        "sharpe":           sharpe_ratio(pct_returns),
        "max_drawdown_%":   max_drawdown(equity_curve),
        "calmar":           calmar_ratio(ret_pct, max_drawdown(equity_curve)),
        "equity_curve":     equity_curve[::10],  # sous-échantillonné
        "final_equity":     round(portfolio.equity, 2),
    }



def compare_strategies(prices: list[float], capital=10_000) -> list[dict]:
    strategies = [
        ("SMA Crossover",  SMACrossover(10, 30)),
        ("RSI Mean Rev.",  RSIStrategy(70, 30)),
        ("MACD",           MACDStrategy()),
        ("Bollinger",      BollingerStrategy()),
        ("Ensemble",       EnsembleStrategy([
            SMACrossover(10, 30), RSIStrategy(70, 30),
            MACDStrategy(), BollingerStrategy()
        ])),
    ]

    results = []
    for name, strategy in strategies:
        res = full_backtest(strategy, prices, capital)
        if "error" not in res:
            results.append({"strategy": name, **res})
            print(f"  {name:20s} | Return={res.get('return_%', 0):+6.1f}% | "
                  f"Sharpe={res.get('sharpe', 0):5.2f} | "
                  f"WR={res.get('win_rate_%', 0):4.1f}% | "
                  f"DD={res.get('max_drawdown_%', 0):4.1f}%")

    return results



def export_results(results: list[dict], filepath: str = "backtest_results.csv"):
    if not results:
        return
    keys = [k for k in results[0] if k != "equity_curve"]
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in results:
            row = {k: r[k] for k in keys}
            writer.writerow(row)
    print(f"\n✅ Résultats exportés → {filepath}")



if __name__ == "__main__":
    print("═" * 65)
    print("  📊 BACKTEST AVANCÉ — Comparaison de stratégies")
    print("═" * 65)

    
    print("\n📈 Marché haussier (trend=+0.02%/jour)")
    prices_bull = generate_price_series(1000, seed=1, trend=0.0002, volatility=0.01)
    results_bull = compare_strategies(prices_bull)


    print("\n📉 Marché baissier (trend=-0.02%/jour)")
    prices_bear = generate_price_series(1000, seed=2, trend=-0.0002, volatility=0.01)
    results_bear = compare_strategies(prices_bear)

    
    print("\n🌊 Marché volatile (volatility=2%)")
    prices_vol = generate_price_series(1000, seed=3, trend=0.0, volatility=0.02)
    results_vol = compare_strategies(prices_vol)

    
    export_results(results_bull, "backtest_bull.csv")
    export_results(results_bear, "backtest_bear.csv")
    export_results(results_vol,  "backtest_volatile.csv")
