"""
config.py  — Configuration centralisée du bot de trading
"""

# ─── Paramètres du bot ──────────────────────────────────────────────────
BOT_CONFIG = {
    "symbol":           "BTC/USDT",   # Paire tradée
    "capital":          10_000,        # Capital initial (USD)
    "interval_sec":     60,            # Intervalle entre chaque bougie (secondes)
    "max_iterations":   1000,          # Nombre max de bougies avant arrêt auto
}

# ─── Paramètres de risque ───────────────────────────────────────────────
RISK_CONFIG = {
    "max_risk_pct":       1.0,   # % du capital risqué par trade
    "max_drawdown_pct":  15.0,   # Stop global si drawdown > X%
    "atr_multiplier":     2.0,   # Multiplicateur ATR pour le stop-loss
    "rr_ratio":           2.0,   # Ratio Risque/Récompense pour le take-profit
}

# ─── Paramètres des stratégies ──────────────────────────────────────────
STRATEGY_CONFIG = {
    "sma_crossover": {"fast": 10, "slow": 30},
    "rsi":           {"period": 14, "overbought": 70, "oversold": 30},
    "macd":          {"fast": 12, "slow": 26, "signal": 9},
    "bollinger":     {"period": 20, "k": 2.0},
}

# ─── Connexion API (Exchange) ────────────────────────────────────────────
# Pour utiliser une vraie API, remplacer ces valeurs et utiliser ccxt :
#   pip install ccxt
#   import ccxt
#   exchange = ccxt.binance({"apiKey": API_KEY, "secret": API_SECRET})

EXCHANGE_CONFIG = {
    "exchange":   "binance",       # binance, kraken, coinbase, alpaca…
    "api_key":    "VOTRE_CLE_API",
    "api_secret": "VOTRE_SECRET",
    "sandbox":    True,            # True = mode test (paper trading réel)
}

# ─── Notifications (optionnel) ───────────────────────────────────────────
NOTIFICATIONS = {
    "telegram_token":  "",  # Token du bot Telegram
    "telegram_chat_id": "", # ID du chat
    "discord_webhook": "",  # URL du webhook Discord
}
