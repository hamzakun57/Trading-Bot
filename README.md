# 🤖 Bot de Trading Python — Guide Complet

## Structure du projet

```
trading_bot/
├── bot.py                  # Moteur principal (tout-en-un)
├── backtest_advanced.py    # Backtest avancé + métriques
├── config.py               # Configuration centralisée
├── requirements.txt        # Dépendances optionnelles
└── README.md               # Ce fichier
```

---

## 🚀 Démarrage rapide

```bash
# Aucune installation nécessaire (Python 3.10+ standard)
python bot.py
```

---

## 🏗️ Architecture

```
MarketData         → Récupère/simule les prix OHLCV
    ↓
Indicators         → Calcule SMA, EMA, RSI, MACD, Bollinger, ATR
    ↓
Strategy           → Génère BUY / SELL / HOLD
    ↓
RiskManager        → Taille de position, Stop-Loss, Take-Profit
    ↓
Portfolio          → Gère cash, positions, trades fermés
    ↓
TradingBot         → Boucle principale + logs
```

---

## 📊 Stratégies incluses

| Stratégie | Principe | Marché idéal |
|-----------|----------|--------------|
| SMA Crossover | Croisement MA rapide/lente | Tendance forte |
| RSI Mean Reversion | Achat sur survente, vente sur surachat | Range / latéral |
| MACD Crossover | Croisement MACD / signal | Tendance modérée |
| Bollinger Bands | Retour à la moyenne | Range / latéral |
| Ensemble (Vote) | Vote majoritaire des 4 stratégies | Tous marchés |

---

## ⚙️ Personnalisation

### Changer la stratégie

```python
from bot import TradingBot, RSIStrategy

bot = TradingBot(
    symbol="ETH/USDT",
    strategy=RSIStrategy(overbought=75, oversold=25),
    capital=5000,
)
bot.run(max_iterations=200)
```

### Connecter un vrai exchange (ccxt)

```python
# pip install ccxt
import ccxt

exchange = ccxt.binance({
    "apiKey": "VOTRE_CLE",
    "secret": "VOTRE_SECRET",
    "sandbox": True,  # Mode test !
})

# Récupérer des bougies réelles
ohlcv = exchange.fetch_ohlcv("BTC/USDT", "1h", limit=100)
prices = [c[4] for c in ohlcv]  # Prix de clôture
```

---

## 📈 Métriques de performance

| Métrique | Description |
|----------|-------------|
| Win Rate | % de trades gagnants |
| Profit Factor | Gains totaux / Pertes totales |
| Sharpe Ratio | Rendement ajusté au risque (>1 = bien, >2 = excellent) |
| Max Drawdown | Pire perte depuis un sommet (viser <15%) |
| Calmar Ratio | Rendement annuel / Max Drawdown |

---

## ⚠️ Avertissements

1. **Ce bot est éducatif**. Ne pas l'utiliser avec de l'argent réel sans tests approfondis.
2. **Le backtesting ≠ performance future**. Les marchés changent.
3. **Gestion du risque TOUJOURS activée**. Ne jamais désactiver les stop-loss.
4. **Commencer en paper trading** avant tout argent réel.
5. **Les performances passées ne garantissent pas les performances futures**.

---

## 🔗 Ressources

- [ccxt Documentation](https://docs.ccxt.com)
- [pandas-ta Indicators](https://github.com/twopirllc/pandas-ta)
- [Alpaca Trading API](https://alpaca.markets/docs/)
- [Binance API](https://binance-docs.github.io/apidocs/)
