# 📚 Documentation Complète — CryptoBot Trading Algorithmique

> **Projet :** Bot de trading Python avec dashboard web temps réel  
> **Stack :** Python 3.11 · FastAPI · WebSocket · HTML/CSS/JS  
> **Mode :** Simulation ou Trading Réel (Bybit via CCXT)

---

# TABLE DES MATIÈRES

1. [Le Trading — Concepts Fondamentaux](#1-le-trading--concepts-fondamentaux)
2. [Les Données de Marché](#2-les-données-de-marché)
3. [Les Indicateurs Techniques](#3-les-indicateurs-techniques)
4. [Les Stratégies de Trading](#4-les-stratégies-de-trading)
5. [La Gestion du Risque](#5-la-gestion-du-risque)
6. [Le Portefeuille et les Positions](#6-le-portefeuille-et-les-positions)
7. [L'Architecture du Projet](#7-larchitecture-du-projet)
8. [Le Bot — Chef d'Orchestre](#8-le-bot--chef-dorchestre)
9. [L'Interface Web et WebSocket](#9-linterface-web-et-websocket)
10. [L'Exchange et les Ordres Réels](#10-lexchange-et-les-ordres-réels)
11. [Les Notifications Discord](#11-les-notifications-discord)
12. [La Stratégie IA (Machine Learning)](#12-la-stratégie-ia-machine-learning)
13. [Le Backtesting](#13-le-backtesting)
14. [Configuration et Démarrage](#14-configuration-et-démarrage)
15. [Flux Complet d'un Trade](#15-flux-complet-dun-trade)

---

---

# 1. Le Trading — Concepts Fondamentaux

## 1.1 Qu'est-ce que le trading ?

Le **trading** consiste à acheter un actif financier (une action, une crypto-monnaie, une devise) à un certain prix, puis à le revendre à un prix différent pour réaliser un **profit ou une perte**.

La différence entre le prix d'achat et le prix de vente s'appelle le **PnL** (Profit and Loss en anglais, soit Profit et Perte).

```
PnL = (prix_vente - prix_achat) × quantité

Exemple :
  Achat  : 0.33 BTC à 67 000$ → coût = 22 110$
  Vente  : 0.33 BTC à 67 900$ → reçu = 22 407$
  PnL    = 22 407 - 22 110 = +297$ (profit)
```

## 1.2 Les marchés crypto

Les cryptomonnaies se négocient sur des **bourses (exchanges)** comme Binance, Bybit, Kraken. On y achète et vend des **paires de trading**.

### Une paire de trading

```
BTC / USDT
 ↑      ↑
Actif  Devise de référence
```

`BTC/USDT` = combien de dollars (USDT = dollar stable) vaut 1 Bitcoin.  
Si BTC/USDT = 67 300$ → 1 Bitcoin se vend 67 300 dollars.

### Autres paires du projet
- `ETH/USDT` — Ethereum / Dollar
- `BTC/USDT` — Bitcoin / Dollar (paire par défaut du bot)

## 1.3 Les positions : Long et Short

| Position | Signification | Quand ouvrir | Quand fermer |
|----------|--------------|--------------|--------------|
| **LONG** | On achète, on parie que le prix **monte** | Prix bas | Prix haut |
| **SHORT** | On vend sans posséder, on parie que le prix **baisse** | Prix haut | Prix bas |

> **Notre bot utilise uniquement des positions LONG** pour rester simple et éviter les risques du short (pertes théoriquement illimitées).

## 1.4 La bougie (Candlestick)

Les prix ne sont pas représentés en valeurs brutes mais sous forme de **bougies japonaises (candlesticks)**. Chaque bougie résume l'évolution du prix sur une période donnée.

```
Structure d'une bougie :

  │  ← Mèche haute (High)
  █
  █  ← Corps (entre Open et Close)
  █
  │  ← Mèche basse (Low)

Champs :
  open      = prix au début de la période
  high      = prix le plus haut atteint
  low       = prix le plus bas atteint
  close     = prix à la fin de la période
  volume    = quantité échangée pendant la période
  timestamp = horodatage de la bougie
```

### En Python (dans ce projet) :

```python
candle = {
    "timestamp": "2024-04-13T19:00:00Z",
    "open":   67100.0,
    "high":   67800.0,
    "low":    66900.0,
    "close":  67342.0,
    "volume": 12500.0
}
```

## 1.5 Le trading manuel vs algorithmique

| Critère | Trading Manuel | Trading Algorithmique |
|---------|---------------|----------------------|
| Vitesse | Secondes | Millisecondes |
| Émotions | Peur, euphorie, indécision | Aucune |
| Disponibilité | Pendant les heures de travail | 24h/24, 7j/7 |
| Cohérence | Variable | Toujours identique |
| Capacité | 1 marché à la fois | Plusieurs marchés simultanés |

Le bot de ce projet est un **bot algorithmique** : il analyse les prix en continu, applique des stratégies mathématiques, et exécute des trades automatiquement.

---

---

# 2. Les Données de Marché

**Fichier :** `core/data.py` — Classe `MarketData`

## 2.1 Rôle

Le module `data.py` est responsable d'une seule chose : **fournir des bougies OHLCV au bot**. Il peut le faire de deux façons :

1. **Mode Réel** → appel API à Bybit pour récupérer les vraies bougies de marché
2. **Mode Simulation** → génération de bougies aléatoires réalistes

## 2.2 Configuration

```python
class MarketData:
    def __init__(self, symbol: str, max_candles: int = 200, use_binance: bool = True):
        self.symbol      = symbol.replace("/", "").upper()  # "BTC/USDT" → "BTCUSDT"
        self.max_candles = max_candles  # Historique max conservé en mémoire
        self.candles     = []           # Liste des bougies
        self.use_binance = use_binance  # True = API Bybit | False = Simulation
```

> **Note :** Le paramètre s'appelle `use_binance` par convention historique, mais l'API utilisée est celle de **Bybit** (v5).

## 2.3 Mode Réel — API Bybit

```python
def _fetch_from_api(self, limit=1) -> list:
    url = f"https://api.bybit.com/v5/market/kline?category=spot&symbol={self.symbol}&interval=1&limit={limit}"
    # Récupère les dernières `limit` bougies d'1 minute
    # Retourne une liste de dicts OHLCV formatés
```

L'API Bybit est publique pour les données de marché — **aucune clé API n'est nécessaire** pour lire les prix.

## 2.4 Mode Simulation — Génération aléatoire

```python
def fetch_candle(self) -> dict:
    prev_close = self.candles[-1]["close"] if self.candles else 100.0

    # Variation aléatoire entre -1.5% et +1.5%
    change = prev_close * random.uniform(-0.015, 0.015)

    open_  = prev_close
    close  = round(open_ + change, 4)
    high   = round(max(open_, close) * random.uniform(1.0, 1.008), 4)
    low    = round(min(open_, close) * random.uniform(0.992, 1.0), 4)
    volume = round(random.uniform(1000, 50000), 2)
```

Chaque nouvelle bougie part du `close` de la précédente → le prix évolue de façon continue et réaliste.

## 2.5 Capacité mémoire

Le bot conserve au maximum **200 bougies** en mémoire (`max_candles=200`). Au-delà, la plus ancienne est supprimée (principe FIFO : First In, First Out).

```python
if len(self.candles) > self.max_candles:
    self.candles.pop(0)  # Supprime la plus ancienne
```

---

---

# 3. Les Indicateurs Techniques

**Fichier :** `core/indicators.py` — Classe `Indicators`

Les indicateurs techniques sont des **formules mathématiques appliquées sur l'historique des prix** pour détecter des patterns, tendances, et zones d'opportunité.

> **Important :** Toutes les formules sont implémentées **de zéro**, sans bibliothèque externe (pas de `pandas-ta`, pas de `talib`).

## 3.1 SMA — Simple Moving Average (Moyenne Mobile Simple)

### Formule
```
SMA(N) = (prix[−N] + prix[−N+1] + ... + prix[−1]) / N
```

### Implémentation
```python
@staticmethod
def sma(prices: list[float], period: int) -> Optional[float]:
    if len(prices) < period:
        return None
    return round(sum(prices[-period:]) / period, 6)
```

### Interprétation
- `SMA(10)` = moyenne des 10 derniers prix → réagit vite aux changements
- `SMA(30)` = moyenne des 30 derniers prix → plus lisse, moins réactif
- Quand `SMA(10) > SMA(30)` → le marché est en **tendance haussière**
- Quand `SMA(10) < SMA(30)` → le marché est en **tendance baissière**

## 3.2 EMA — Exponential Moving Average (Moyenne Mobile Exponentielle)

### Différence avec SMA
L'EMA donne plus de **poids aux prix récents** grâce à un facteur multiplicatif `k`.

### Formule
```
k = 2 / (period + 1)
EMA(t) = prix(t) × k + EMA(t-1) × (1 - k)
```

### Implémentation
```python
@staticmethod
def ema(prices: list[float], period: int) -> Optional[float]:
    k = 2 / (period + 1)
    ema_val = sum(prices[:period]) / period  # Initialisation avec SMA
    for price in prices[period:]:
        ema_val = price * k + ema_val * (1 - k)
    return round(ema_val, 6)
```

### Utilisation dans le projet
L'EMA est la brique de base du MACD (voir section 3.4).

## 3.3 RSI — Relative Strength Index

### Concept
Le RSI mesure la **force relative des hausses par rapport aux baisses** sur une période. Il oscille entre 0 et 100.

### Formule
```
Pour chaque période :
  - Si prix monte → gain = différence, perte = 0
  - Si prix baisse → gain = 0, perte = différence

RS    = moyenne_gains / moyenne_pertes
RSI   = 100 − (100 / (1 + RS))
```

### Implémentation
```python
@staticmethod
def rsi(prices: list[float], period: int = 14) -> Optional[float]:
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
```

### Interprétation
| Valeur RSI | Signal | Signification |
|-----------|--------|---------------|
| < 30 | **BUY** 🟢 | Survente — le marché a trop baissé |
| 30 – 70 | **HOLD** | Zone neutre |
| > 70 | **SELL** 🔴 | Surachat — le marché a trop monté |

## 3.4 MACD — Moving Average Convergence Divergence

### Concept
Le MACD mesure la **dynamique (momentum)** de la tendance. Il est composé de 3 éléments :
- **Ligne MACD** = EMA(12) - EMA(26)
- **Ligne Signal** = EMA(9) de la ligne MACD
- **Histogramme** = MACD - Signal

### Implémentation
```python
@staticmethod
def macd(prices, fast=12, slow=26, signal=9):
    ema_fast = Indicators.ema(prices, fast)   # EMA des 12 dernières bougies
    ema_slow = Indicators.ema(prices, slow)   # EMA des 26 dernières bougies
    macd_line = ema_fast - ema_slow           # Différence entre les deux
    # Signal = moyenne du MACD sur 9 périodes
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram
```

### Interprétation
- Histogramme passe de **négatif à positif** → BUY (momentum haussier)
- Histogramme passe de **positif à négatif** → SELL (momentum baissier)

## 3.5 Bollinger Bands (Bandes de Bollinger)

### Concept
Les bandes de Bollinger créent un **canal statistique** autour du prix. Quand le prix sort du canal, il a tendance à y revenir.

### Formule
```
Bande Centrale (Mid) = SMA(20)
Écart-type (σ)       = std des 20 derniers prix
Bande Haute          = Mid + 2σ
Bande Basse          = Mid - 2σ
```

### Implémentation
```python
@staticmethod
def bollinger_bands(prices, period=20, k=2.0):
    window = prices[-period:]
    mid = sum(window) / period
    std = (sum((x - mid) ** 2 for x in window) / period) ** 0.5
    return round(mid - k * std, 4), round(mid, 4), round(mid + k * std, 4)
    #           Bande Basse             Milieu           Bande Haute
```

### Interprétation
- Prix < Bande Basse → **BUY** (le prix est trop bas, retour à la moyenne probable)
- Prix > Bande Haute → **SELL** (le prix est trop haut, retour à la moyenne probable)

## 3.6 ATR — Average True Range (Volatilité)

### Concept
L'ATR mesure la **volatilité moyenne du marché** sur une période. C'est l'indicateur le plus utilisé pour calibrer les Stop-Loss.

### Formule
```
Pour chaque bougie :
  TR = max(High - Low, |High - Close_précédent|, |Low - Close_précédent|)

ATR = moyenne des TR sur les N dernières bougies
```

### Implémentation
```python
@staticmethod
def atr(candles: list[dict], period=14) -> Optional[float]:
    trs = []
    for i in range(1, len(candles)):
        h, l, pc = candles[i]["high"], candles[i]["low"], candles[i-1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return round(sum(trs[-period:]) / period, 4)
```

### Utilisation dans ce projet
```python
# Dans bot.py → _execute_signal()
atr = Indicators.atr(self.data.candles)
# ATR = 150$ → Stop-Loss = prix - 2 × 150 = prix - 300$
# Plus l'ATR est grand, plus le marché est volatile, plus le stop est loin
```

---

---

# 4. Les Stratégies de Trading

**Fichier :** `core/strategies.py`

## 4.1 Architecture des stratégies

Toutes les stratégies héritent d'une classe de base `Strategy` :

```python
class Signal:
    BUY  = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class Strategy:
    """Classe de base — toutes les stratégies doivent implémenter generate()"""
    name = "Base"
    def generate(self, data: MarketData) -> str:
        raise NotImplementedError
        # Retourne toujours : Signal.BUY, Signal.SELL, ou Signal.HOLD
```

## 4.2 SMACrossover — Croisement de Moyennes Mobiles

### Principe
Détecte le moment où la **moyenne rapide croise la moyenne lente**.

```
SMA_rapide(10) croise SMA_lente(30) vers le haut → BUY
SMA_rapide(10) croise SMA_lente(30) vers le bas  → SELL
```

### Paramètres par défaut
- `fast = 10` (ou `2` en mode ultra-réactif pour la démo)
- `slow = 30` (ou `4` en mode ultra-réactif pour la démo)

### Implémentation complète
```python
class SMACrossover(Strategy):
    name = "SMA Crossover"

    def __init__(self, fast=10, slow=30):
        self.fast, self.slow = fast, slow

    def generate(self, data: MarketData) -> str:
        closes = data.closes()  # Liste de tous les prix de clôture

        sma_f = Indicators.sma(closes, self.fast)   # SMA actuelle rapide
        sma_s = Indicators.sma(closes, self.slow)   # SMA actuelle lente

        if not sma_f or not sma_s:
            return Signal.HOLD  # Pas assez de données

        # SMA de la bougie précédente (pour détecter le croisement)
        prev_closes = closes[:-1]
        prev_f = Indicators.sma(prev_closes, self.fast)
        prev_s = Indicators.sma(prev_closes, self.slow)

        if prev_f and prev_s:
            # Croisement vers le haut : avant (lente > rapide), maintenant (rapide > lente)
            if prev_f <= prev_s and sma_f > sma_s:
                return Signal.BUY

            # Croisement vers le bas : avant (rapide > lente), maintenant (lente > rapide)
            if prev_f >= prev_s and sma_f < sma_s:
                return Signal.SELL

        return Signal.HOLD
```

### Marché idéal
Marchés en **forte tendance** (bull market ou bear market). Inefficace en marché plat.

## 4.3 RSIStrategy — Mean Reversion (Retour à la Moyenne)

### Principe
Achète quand le marché est **épuisé à la baisse** (survente), vend quand il est **épuisé à la hausse** (surachat).

```python
class RSIStrategy(Strategy):
    name = "RSI Mean Reversion"

    def __init__(self, overbought=70, oversold=30, period=14):
        self.overbought = overbought  # Seuil de surachat (défaut: 70)
        self.oversold   = oversold    # Seuil de survente (défaut: 30)
        self.period     = period      # Période de calcul (défaut: 14)

    def generate(self, data: MarketData) -> str:
        rsi = Indicators.rsi(data.closes(), self.period)

        if rsi is None:
            return Signal.HOLD   # Pas assez de données

        if rsi < self.oversold:   # Ex: RSI = 25 < 30 → marché survendu
            return Signal.BUY

        if rsi > self.overbought: # Ex: RSI = 75 > 70 → marché suracheté
            return Signal.SELL

        return Signal.HOLD        # Zone neutre (30 < RSI < 70)
```

### Marché idéal
Marchés **latéraux (range)** qui oscillent sans direction claire.

## 4.4 MACDStrategy — Croisement MACD

### Principe
Détecte le changement de **momentum** (élan) via le renversement de l'histogramme MACD.

```python
class MACDStrategy(Strategy):
    name = "MACD Crossover"

    def generate(self, data: MarketData) -> str:
        closes = data.closes()

        result      = Indicators.macd(closes)         # MACD actuel
        prev_result = Indicators.macd(closes[:-1])    # MACD bougie précédente

        if not result or not prev_result:
            return Signal.HOLD

        _, _, hist      = result      # Histogramme actuel
        _, _, prev_hist = prev_result # Histogramme précédent

        # Histogramme passe de négatif à positif → élan haussier
        if prev_hist < 0 and hist > 0:
            return Signal.BUY

        # Histogramme passe de positif à négatif → élan baissier
        if prev_hist > 0 and hist < 0:
            return Signal.SELL

        return Signal.HOLD
```

### Marché idéal
Marchés en **tendance modérée**, transitions entre phases.

## 4.5 BollingerStrategy — Retour à la Moyenne

### Principe
Détecte quand le prix s'éloigne trop de sa **moyenne statistique** et va probablement y revenir.

```python
class BollingerStrategy(Strategy):
    name = "Bollinger Bands"

    def generate(self, data: MarketData) -> str:
        closes = data.closes()
        result = Indicators.bollinger_bands(closes)

        if not result:
            return Signal.HOLD

        lower, mid, upper = result  # Bande basse, milieu, bande haute
        price = closes[-1]          # Prix actuel

        if price < lower:   # Prix sous la bande basse → trop bas
            return Signal.BUY

        if price > upper:   # Prix au-dessus de la bande haute → trop haut
            return Signal.SELL

        return Signal.HOLD
```

### Marché idéal
Marchés **volatils mais sans tendance**, oscillant dans un range.

## 4.6 EnsembleStrategy — Vote Majoritaire

### Principe
Au lieu de choisir une seule stratégie, l'Ensemble **combine plusieurs stratégies** et prend la décision qui obtient le plus de votes.

```python
class EnsembleStrategy(Strategy):
    name = "Ensemble (Vote)"

    def __init__(self, strategies: list):
        self.strategies = strategies

    def generate(self, data: MarketData) -> str:
        votes = {Signal.BUY: 0, Signal.SELL: 0, Signal.HOLD: 0}

        for s in self.strategies:
            signal = s.generate(data)
            votes[signal] += 1

        # Retourne le signal avec le plus de votes
        return max(votes, key=votes.get)
```

### Configuration dans web_app.py
```python
EnsembleStrategy([
    SMACrossover(10, 30),
    RSIStrategy(70, 30),
    MACDStrategy(),
    BollingerStrategy()
])

# Exemple de vote :
# SMA Cross  → BUY
# RSI        → HOLD
# MACD       → BUY
# Bollinger  → BUY
# Résultat   → BUY (3 votes sur 4)
```

### Avantage
Réduit les **faux signaux** individuels. Une stratégie seule peut se tromper, mais 3 stratégies sur 4 qui s'accordent donnent un signal plus fiable.

## 4.7 Tableau comparatif des stratégies

| Stratégie | Marché idéal | Vitesse signal | Fiabilité |
|-----------|-------------|---------------|-----------|
| SMA Crossover | Tendance forte | Lent | Moyen |
| RSI Mean Reversion | Range / Latéral | Moyen | Bon |
| MACD Crossover | Tendance modérée | Moyen | Bon |
| Bollinger Bands | Range / Volatile | Rapide | Moyen |
| Ensemble (Vote) | Tous marchés | Moyen | Meilleur |
| AI Random Forest | Habitué aux données | Variable | Dépend des données |

---

---

# 5. La Gestion du Risque

**Fichier :** `core/portfolio.py` — Classe `RiskManager`

## 5.1 La règle d'or du trading

> **Protéger le capital AVANT de chercher des profits.**

Un trader professionnel ne pense pas "combien je peux gagner ?" mais "combien je peux perdre ?". Le `RiskManager` automatise entièrement cette logique.

## 5.2 Stop-Loss — Couper les pertes

### Définition
Le **Stop-Loss** est un prix seuil : si le prix descend jusqu'à ce niveau, la position est fermée automatiquement pour éviter une perte encore plus grande.

### Formule utilisée (basée sur ATR)
```python
def stop_loss(self, entry: float, atr: float, side: str = "long", multiplier=2.0) -> float:
    if side == "long":
        return round(entry - multiplier * atr, 4)
    return round(entry + multiplier * atr, 4)
```

### Exemple concret
```
Entrée  = 67 300$
ATR     = 150$ (volatilité actuelle)
Stop-Loss = 67 300 - 2 × 150 = 67 000$

→ Si BTC descend à 67 000$, le bot vend immédiatement.
→ Perte maximale sur ce trade = 300$ par BTC
```

**Pourquoi 2×ATR ?** L'ATR mesure le mouvement normal du marché. Un stop à 2×ATR laisse au prix un peu de marge pour respirer sans déclencher le stop sur du bruit normal.

## 5.3 Take-Profit — Verrouiller les gains

### Définition
Le **Take-Profit** est le prix cible : quand le prix l'atteint, la position est fermée automatiquement pour sécuriser le profit.

### Formule (ratio Risque/Récompense)
```python
def take_profit(self, entry: float, stop: float, rr_ratio=2.0) -> float:
    distance = abs(entry - stop)   # Distance au Stop-Loss
    if entry > stop:
        return round(entry + rr_ratio * distance, 4)
```

### Exemple concret
```
Entrée    = 67 300$
Stop-Loss = 67 000$
Distance  = 300$
RR Ratio  = 2.0

Take-Profit = 67 300 + 2.0 × 300 = 67 900$

→ On risque 300$ pour gagner 600$
→ Ratio Risque/Récompense = 1:2
```

**Pourquoi un ratio 1:2 ?** Même si le bot perd 1 trade sur 2, il reste profitable :  
`50% × 600$ − 50% × 300$ = +150$ de profit par série de 2 trades.`

## 5.4 Position Size — Ne pas jouer quitte ou double

### Définition
La **taille de position** détermine combien acheter. L'objectif est de ne risquer qu'une petite fraction du capital à chaque trade.

### Formule
```python
def position_size(self, capital: float, entry: float, stop_loss: float) -> float:
    risk_amount = capital * (self.max_risk_pct / 100)  # 1% de 10 000$ = 100$
    distance    = abs(entry - stop_loss)               # Distance en dollars
    qty         = risk_amount / distance               # Quantité à acheter
    max_qty     = capital / entry                      # Max = tout le capital
    return min(qty, max_qty)                           # On prend le minimum
```

### Exemple concret
```
Capital     = 10 000$
Risque      = 1% = 100$
Entrée      = 67 300$
Stop-Loss   = 67 000$
Distance    = 300$

Quantité    = 100$ / 300$ = 0.333 BTC

Coût total  = 0.333 × 67 300 = 22 410$   (22% du capital)
Perte max   = 0.333 × 300   = 100$       (1% du capital)
Gain cible  = 0.333 × 600   = 200$       (2% du capital)
```

## 5.5 Max Drawdown — Filet de sécurité global

### Définition
Le **drawdown** est la perte maximale depuis le dernier sommet de capital. Si les pertes cumulées dépassent un seuil, le bot s'arrête complètement.

```python
def check_drawdown(self, equity: float) -> bool:
    if self.peak_equity is None or equity > self.peak_equity:
        self.peak_equity = equity  # Nouveau sommet enregistré

    dd_pct = (self.peak_equity - equity) / self.peak_equity * 100

    if dd_pct >= self.max_drawdown_pct:  # Défaut: 15%
        log.warning(f"⚠️ Max drawdown atteint : {dd_pct:.1f}%")
        return False  # → Bot s'arrête

    return True
```

### Exemple
```
Capital initial = 10 000$
Sommet atteint  = 10 500$
Capital actuel  = 8 925$

Drawdown = (10 500 - 8 925) / 10 500 × 100 = 15%
→ Seuil atteint → Bot s'arrête automatiquement
```

---

---

# 6. Le Portefeuille et les Positions

**Fichier :** `core/portfolio.py` — Classes `Position` et `Portfolio`

## 6.1 La classe Position

Une `Position` représente un **trade en cours** (ouvert mais pas encore fermé).

```python
class Position:
    def __init__(self, symbol, side, qty, entry, stop, tp, timestamp=None):
        self.symbol    = symbol    # "BTC/USDT"
        self.side      = side      # "long"
        self.qty       = qty       # 0.333 BTC
        self.entry     = entry     # 67 300$ (prix d'achat)
        self.stop      = stop      # 67 000$ (Stop-Loss)
        self.tp        = tp        # 67 900$ (Take-Profit)
        self.timestamp = timestamp # Horodatage d'ouverture
        self.pnl       = 0.0       # Profit/Perte actualisé en temps réel

    def update_pnl(self, current_price: float):
        # PnL non-réalisé = (prix actuel - prix d'entrée) × quantité
        self.pnl = (current_price - self.entry) * self.qty
        return self.pnl
```

## 6.2 La classe Portfolio

Le `Portfolio` gère le **capital, les positions ouvertes, et l'historique des trades**.

```python
class Portfolio:
    def __init__(self, initial_capital: float = 10_000):
        self.cash            = initial_capital  # Liquidités disponibles
        self.initial_capital = initial_capital  # Capital de départ
        self.positions       = {}              # Positions ouvertes {symbol: Position}
        self.closed_trades   = []              # Historique des trades fermés

    @property
    def equity(self):
        # Valeur totale = cash + valeur de marché de toutes les positions
        return self.cash + sum((p.entry * p.qty) + p.pnl for p in self.positions.values())
```

### Ouverture d'une position
```python
def open_position(self, pos: Position) -> bool:
    cost = pos.entry * pos.qty       # Coût en dollars

    if cost > self.cash + 1e-6:      # Vérification du capital disponible
        log.warning("Capital insuffisant")
        return False

    self.cash -= cost                # Déduction du cash
    self.positions[pos.symbol] = pos # Enregistrement de la position

    # → Envoi alerte Discord
    # → Envoi ordre réel à Bybit (si API configurée)
    return True
```

### Fermeture d'une position
```python
def close_position(self, symbol: str, price: float, reason: str = "signal"):
    pos = self.positions.pop(symbol, None)  # Retrait des positions actives

    proceeds = price * pos.qty     # Montant encaissé
    self.cash += proceeds          # Ajout au cash
    pnl = pos.update_pnl(price)    # Calcul du profit/perte final

    self.closed_trades.append({    # Enregistrement dans l'historique
        "symbol": symbol,
        "entry":  pos.entry,
        "exit":   price,
        "pnl":    round(pnl, 2),
        "reason": reason           # "stop-loss", "take-profit", "signal", "manual-close"
    })
```

### Statistiques
```python
def stats(self) -> dict:
    pnls = [t["pnl"] for t in self.closed_trades]
    wins = [p for p in pnls if p > 0]

    return {
        "total_trades":  len(pnls),
        "win_rate_%":    len(wins) / len(pnls) * 100,  # % de trades gagnants
        "total_pnl":     sum(pnls),                    # Profit total
        "profit_factor": abs(sum(wins) / sum(losses)), # Gains / Pertes
        "equity":        self.equity                   # Capital total actuel
    }
```

---

---

# 7. L'Architecture du Projet

## 7.1 Vue d'ensemble

```
projet python/
│
├── web_app.py              ← Point d'entrée web (FastAPI + WebSocket)
├── config.py               ← Configuration centralisée
├── requirements.txt        ← Dépendances Python
│
├── core/                   ← Moteur du bot (logique métier)
│   ├── __init__.py
│   ├── data.py             ← Récupération des données de marché
│   ├── indicators.py       ← Calcul des indicateurs (SMA, RSI, MACD...)
│   ├── strategies.py       ← Logique de décision (BUY / SELL / HOLD)
│   ├── portfolio.py        ← Gestion capital, positions, risque
│   ├── bot.py              ← Chef d'orchestre (boucle principale)
│   ├── exchange.py         ← Connexion Bybit via CCXT (ordres réels)
│   ├── notifications.py    ← Alertes Discord via Webhook
│   └── ai_model.py         ← Stratégie Machine Learning (Random Forest)
│
└── static/                 ← Interface web
    ├── index.html          ← Dashboard principal
    ├── presentation.html   ← Présentation interactive
    ├── css/
    │   └── style.css       ← Styles du dashboard
    └── js/
        └── app.js          ← Logique frontend (graphiques, WebSocket)
```

## 7.2 Les couches d'architecture

```
┌─────────────────────────────────────────┐
│   COUCHE PRÉSENTATION                   │
│   web_app.py + static/                  │   ← Interface utilisateur
│   FastAPI · WebSocket · HTML/JS         │
├─────────────────────────────────────────┤
│   COUCHE BOT (Chef d'orchestre)         │
│   core/bot.py                           │   ← Coordination
│   core/data.py                          │   ← Données
├─────────────────────────────────────────┤
│   COUCHE ANALYSE                        │
│   core/indicators.py                    │   ← Calculs mathématiques
│   core/strategies.py                    │   ← Décisions de trading
│   core/ai_model.py                      │   ← IA / Machine Learning
├─────────────────────────────────────────┤
│   COUCHE EXÉCUTION                      │
│   core/portfolio.py (RiskManager)       │   ← Gestion du risque
│   core/portfolio.py (Portfolio)         │   ← Gestion du capital
│   core/exchange.py                      │   ← Ordres réels (Bybit)
│   core/notifications.py                 │   ← Alertes Discord
└─────────────────────────────────────────┘
```

## 7.3 Pattern Singleton

Les classes `ExchangeManager` et `NotificationManager` utilisent le **pattern Singleton** : une seule instance existe dans tout le programme.

```python
class ExchangeManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.exchange = None
        return cls._instance  # ← Toujours la même instance

# Usage partout dans le projet :
exchange_client = ExchangeManager()  # core/exchange.py
# ↑ Cette variable est importée et utilisée dans portfolio.py
# ↑ C'est toujours la même instance, configurée une seule fois
```

**Pourquoi ?** La connexion à Bybit est coûteuse à établir. On la crée une fois et on la réutilise partout, sans la passer en paramètre à chaque fonction.

---

---

# 8. Le Bot — Chef d'Orchestre

**Fichier :** `core/bot.py` — Classe `TradingBot`

## 8.1 Initialisation

```python
class TradingBot:
    def __init__(self, symbol: str, strategy: Strategy, capital: float = 10_000, interval_sec: int = 5):
        self.symbol    = symbol           # Paire tradée ("BTC/USDT")
        self.strategy  = strategy         # Stratégie de trading active
        self.interval  = interval_sec     # Délai entre deux ticks (secondes)
        self.data      = MarketData(symbol)       # Module données
        self.portfolio = Portfolio(capital)        # Module portefeuille
        self.risk_mgr  = RiskManager(max_risk_pct=1.0, max_drawdown_pct=99.0)
        self.running   = False            # État du bot (on/off)
        self.iteration = 0                # Compteur de bougies traitées

        # Callbacks pour le dashboard (appelés après chaque bougie/trade)
        self.on_candle_cb = None
        self.on_trade_cb  = None
```

## 8.2 La méthode tick() — Le cœur du bot

```python
def tick(self) -> dict:
    """Une itération complète du bot."""

    # 1. Récupérer une nouvelle bougie
    candle = self.data.fetch_candle()
    price  = candle["close"]
    self.iteration += 1

    # 2. Vérifier le drawdown global (sécurité)
    if not self.risk_mgr.check_drawdown(self.portfolio.equity):
        self.running = False  # Arrêt si pertes globales trop importantes
        return candle

    # 3. Vérifier les sorties automatiques (Stop-Loss / Take-Profit)
    self._check_exits(price)

    # 4. Générer un signal si assez de données (minimum 35 bougies)
    if len(self.data.candles) >= 35:
        signal = self.strategy.generate(self.data)

        if signal != Signal.HOLD:
            self._execute_signal(signal, price)

    # 5. Notifier le dashboard via callback
    if self.on_candle_cb:
        self.on_candle_cb({
            "candle": candle,
            "portfolio": {
                "equity":    self.portfolio.equity,
                "cash":      self.portfolio.cash,
                "stats":     self.portfolio.stats(),
                "positions": [p.to_dict() for p in self.portfolio.positions.values()]
            }
        })

    return candle
```

## 8.3 Vérification des sorties automatiques

```python
def _check_exits(self, price: float):
    pos = self.portfolio.positions.get(self.symbol)
    if not pos:
        return  # Pas de position ouverte → rien à faire

    pos.update_pnl(price)  # Mise à jour PnL non-réalisé

    if pos.side == "long":
        if price <= pos.stop:  # Prix descend sous le Stop-Loss
            self.portfolio.close_position(self.symbol, price, "stop-loss")

        elif price >= pos.tp:  # Prix atteint le Take-Profit
            self.portfolio.close_position(self.symbol, price, "take-profit")
```

## 8.4 Exécution d'un signal

```python
def _execute_signal(self, signal: str, price: float):
    atr = Indicators.atr(self.data.candles)
    if atr is None:
        atr = price * 0.01  # ATR de secours = 1% du prix

    if signal == Signal.BUY and self.symbol not in self.portfolio.positions:
        # Calculer Stop-Loss, Take-Profit, et quantité
        stop = self.risk_mgr.stop_loss(price, atr, "long")
        tp   = self.risk_mgr.take_profit(price, stop)
        qty  = self.risk_mgr.position_size(self.portfolio.equity, price, stop)

        if qty > 0:
            pos = Position(self.symbol, "long", qty, price, stop, tp)
            self.portfolio.open_position(pos)  # → Discord + Bybit + Dashboard

    elif signal == Signal.SELL:
        if self.symbol in self.portfolio.positions:
            self.portfolio.close_position(self.symbol, price, "signal")
```

---

---

# 9. L'Interface Web et WebSocket

**Fichier :** `web_app.py`

## 9.1 Pourquoi FastAPI + WebSocket ?

- **FastAPI** : framework Python ultra-rapide pour créer des APIs web, avec support natif de l'async
- **WebSocket** : protocole de communication bidirectionnel en temps réel (contrairement à HTTP qui est unidirectionnel)

Avec HTTP classique, le navigateur doit **demander** les mises à jour (polling). Avec WebSocket, le serveur **pousse** les mises à jour automatiquement → idéal pour un dashboard trading en temps réel.

## 9.2 ConnectionManager — Gestion des connexions

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

        # Envoi de l'état complet au nouveau client
        initial_state = {
            "type":    "init",
            "candles": bot.data.candles,         # Tout l'historique des bougies
            "portfolio": { ... }
        }
        await websocket.send_json(initial_state)

    async def broadcast(self, message: dict):
        # Envoi du message à TOUS les clients connectés
        for connection in self.active_connections:
            await connection.send_json(message)
```

## 9.3 Boucle du bot en arrière-plan

```python
async def run_bot_loop():
    """Tâche asynchrone qui tourne en permanence."""
    while True:
        if bot.running:
            candle = bot.tick()  # Avance d'une bougie

            # Diffusion de l'état à tous les clients WebSocket
            state = {
                "type":      "update",
                "candle":    candle,
                "portfolio": {
                    "equity":        bot.portfolio.equity,
                    "cash":          bot.portfolio.cash,
                    "stats":         bot.portfolio.stats(),
                    "positions":     [...],
                    "closed_trades": bot.portfolio.closed_trades
                }
            }
            await manager.broadcast(state)

        await asyncio.sleep(1)  # Mise à jour toutes les secondes

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_bot_loop())  # Lance en arrière-plan au démarrage
```

## 9.4 Commandes reçues depuis le dashboard

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    while True:
        data = await websocket.receive_text()
        msg  = json.loads(data)

        if msg["command"] == "start":
            bot.running = True

        elif msg["command"] == "stop":
            bot.running = False

        elif msg["command"] == "set_strategy":
            val = msg["value"]
            if val == "aggressive":
                bot.strategy = SMACrossover(2, 4)       # Ultra-réactif
            elif val == "moderate":
                bot.strategy = SMACrossover(10, 30)     # Standard
            elif val == "ai":
                bot.strategy = MLAIStrategy()           # Machine Learning
            else:  # "ensemble"
                bot.strategy = EnsembleStrategy([...])  # Vote de 4 stratégies

        elif msg["command"] == "manual_trade":
            side = msg["side"]  # "long" ou "short"
            price = bot.data.candles[-1]["close"]
            bot._execute_signal(Signal.BUY if side == "long" else Signal.SELL, price)

        elif msg["command"] == "close_position":
            sym = msg["symbol"]
            price = bot.data.candles[-1]["close"]
            bot.portfolio.close_position(sym, price, "manual-close")

        elif msg["command"] == "update_settings":
            bot.risk_mgr.max_risk_pct = msg["risk"]
            notifier.set_discord_webhook(msg["discord"])
            exchange_client.initialize(msg["api_key"], msg["api_secret"], testnet=True)

        elif msg["command"] == "run_backtest":
            prices = [c["close"] for c in bot.data.candles]
            stats  = Backtester(bot.strategy).run(prices)
            await websocket.send_json({"type": "backtest_result", "stats": stats})
```

---

---

# 10. L'Exchange et les Ordres Réels

**Fichier :** `core/exchange.py` — Classe `ExchangeManager`

## 10.1 Mode simulation vs mode réel

```python
def create_market_order(self, symbol: str, side: str, amount: float):
    if not self.exchange:
        # Mode simulation : aucune clé API configurée
        log.warning(f"[Simulation CCXT] Ordre {side} sur {symbol} de {amount}")
        return True  # ← Simule un succès sans rien faire

    # Mode réel : envoi de l'ordre à Bybit
    order = self.exchange.create_market_order(symbol, side, amount)
    return order
```

## 10.2 Connexion à Bybit (CCXT)

```python
def initialize(self, api_key: str, api_secret: str, testnet: bool = True):
    import ccxt
    self.exchange = ccxt.bybit({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })

    if testnet:
        self.exchange.set_sandbox_mode(True)  # ← Mode Testnet (argent fictif)

    self.exchange.fetch_balance()  # Test de connexion
    return True
```

**CCXT** (Crypto Currency eXchange Trading Library) est une bibliothèque Python qui unifie l'accès à 100+ exchanges différents avec une API identique.

## 10.3 Déclenchement automatique

Dans `portfolio.py`, à chaque ouverture et fermeture :

```python
# À l'ouverture d'une position LONG :
exchange_client.create_market_order(pos.symbol, "buy", pos.qty)

# À la fermeture d'une position LONG :
exchange_client.create_market_order(symbol, "sell", pos.qty)
```

---

---

# 11. Les Notifications Discord

**Fichier :** `core/notifications.py` — Classe `NotificationManager`

## 11.1 Fonctionnement

Discord propose des **Webhooks** : des URLs spéciales qui permettent à n'importe quel programme d'envoyer des messages dans un channel Discord via une simple requête HTTP POST.

```python
def send_discord_message(self, message: str, color: int = 0x00E676):
    payload = {
        "embeds": [{
            "title":       "🤖 CryptoBot Alert",
            "description": message,
            "color":       color   # 0x00E676 = vert | 0xFF1744 = rouge
        }]
    }
    requests.post(self.discord_webhook_url, json=payload, timeout=5)
```

## 11.2 Alertes envoyées automatiquement

**À l'ouverture d'une position :**
```
🟢 NOUVELLE POSITION LONG
Paire: BTC/USDT
Prix d'entrée: $67300
Quantité: 0.3330
SL: $67000 | TP: $67900
```

**À la fermeture d'une position :**
```
POSITION FERMÉE
Paire: BTC/USDT
Prix de sortie: $67900
Raison: take-profit
PnL: +199.80$ ✅
```

## 11.3 Configuration

Depuis le dashboard Settings ou via `config.py` :
```python
notifier.set_discord_webhook("https://discord.com/api/webhooks/XXXX/YYYY")
```

---

---

# 12. La Stratégie IA (Machine Learning)

**Fichier :** `core/ai_model.py` — Classe `MLAIStrategy`

## 12.1 Modèle utilisé : Random Forest

Le **Random Forest** est un algorithme de classification basé sur un ensemble d'arbres de décision. Chaque arbre vote, et la majorité l'emporte.

```python
self.model = RandomForestClassifier(
    n_estimators=100,  # 100 arbres de décision
    max_depth=5,       # Profondeur max de chaque arbre
    random_state=42    # Seed pour reproductibilité
)
```

## 12.2 Features (variables d'entrée)

```python
def _prepare_features(self, candles: list):
    df = pd.DataFrame(candles)

    df['return'] = df['close'].pct_change()        # Rendement = variation % du prix
    df['sma_10'] = df['close'].rolling(10).mean()  # Moyenne mobile 10 périodes
    df['sma_30'] = df['close'].rolling(30).mean()  # Moyenne mobile 30 périodes

    # Target = 1 si le prochain prix est > prix actuel (hausse), 0 sinon
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)

    return df.dropna()
```

**3 variables d'entrée (features) :**
1. `return` — Le rendement de la dernière bougie (montée ou descente)
2. `sma_10` — Niveau de la moyenne mobile courte
3. `sma_30` — Niveau de la moyenne mobile longue

## 12.3 Entraînement et prédiction

```python
def generate(self, data: MarketData) -> str:
    # S'entraîner au premier appel
    if not self.is_trained:
        self._train_model(data.candles)  # Besoin de 50 bougies minimum

    if not self.is_trained:
        return Signal.HOLD  # Pas encore formé

    # Prédire sur la dernière bougie
    last_row = df.iloc[-1]
    pred = self.model.predict(X_pred)[0]

    if pred == 1:  # Le modèle prédit une hausse
        return Signal.BUY
    elif pred == 0:  # Le modèle prédit une baisse
        return Signal.SELL

    return Signal.HOLD
```

**Limitation :** Le modèle est entraîné sur les données de simulation, pas sur de vraies données historiques. En production, il faudrait l'entraîner sur des années de données.

---

---

# 13. Le Backtesting

**Fichier :** `core/portfolio.py` — Classe `Backtester`

## 13.1 Qu'est-ce que le backtesting ?

Le backtesting consiste à **rejouer une stratégie sur des données passées** pour évaluer comment elle aurait performé dans le passé.

> ⚠️ Les performances passées ne garantissent pas les performances futures.

## 13.2 Fonctionnement

```python
class Backtester:
    def __init__(self, strategy: Strategy, capital=10_000, atr_multiplier=2.0, rr_ratio=2.0):
        self.strategy = strategy
        self.capital  = capital

    def run(self, prices: list[float]) -> dict:
        portfolio = Portfolio(self.capital)
        risk_mgr  = RiskManager()
        data      = MarketData("BT")  # Données de backtest

        for price in prices:  # ← Rejoue chaque bougie historique
            # Construire une bougie artificielle
            candle = {"open": price, "high": price * 1.002, "low": price * 0.998, "close": price, ...}
            data.candles.append(candle)

            # Vérifier les exits (SL/TP)
            if position ouverte:
                if price <= pos.stop: fermer("stop-loss")
                if price >= pos.tp:   fermer("take-profit")

            # Générer signal
            signal = self.strategy.generate(data)

            if signal == Signal.BUY:
                ouvrir_position(...)
            elif signal == Signal.SELL:
                fermer_position(...)

        return portfolio.stats()  # Win Rate, PnL total, etc.
```

## 13.3 Métriques de performance

| Métrique | Formule | Objectif |
|----------|---------|---------|
| **Win Rate** | trades gagnants / total trades × 100 | > 50% |
| **Total PnL** | somme de tous les PnL | > 0 |
| **Profit Factor** | somme gains / somme pertes | > 1.5 |
| **Equity Final** | capital initial + PnL total | > capital initial |

---

---

# 14. Configuration et Démarrage

**Fichier :** `config.py`

## 14.1 Paramètres disponibles

```python
BOT_CONFIG = {
    "symbol":        "BTC/USDT",  # Paire tradée
    "capital":       10_000,      # Capital initial ($)
    "interval_sec":  60,          # Délai entre bougies (secondes)
    "max_iterations": 1000,       # Nombre max de bougies avant arrêt
}

RISK_CONFIG = {
    "max_risk_pct":     1.0,  # % risqué par trade
    "max_drawdown_pct": 15.0, # Seuil de drawdown global
    "atr_multiplier":   2.0,  # Multiplicateur ATR pour Stop-Loss
    "rr_ratio":         2.0,  # Ratio Risque/Récompense
}

STRATEGY_CONFIG = {
    "sma_crossover": {"fast": 10, "slow": 30},
    "rsi":           {"period": 14, "overbought": 70, "oversold": 30},
    "macd":          {"fast": 12, "slow": 26, "signal": 9},
    "bollinger":     {"period": 20, "k": 2.0},
}

EXCHANGE_CONFIG = {
    "api_key":    "VOTRE_CLE_API",
    "api_secret": "VOTRE_SECRET",
    "sandbox":    True,  # True = Testnet (argent fictif)
}

NOTIFICATIONS = {
    "discord_webhook": "",  # URL webhook Discord
}
```

## 14.2 Lancement

### Dashboard Web (recommandé)
```bash
pip install -r requirements.txt
python web_app.py
# → Ouvrir http://localhost:8000
```

### Mode terminal uniquement
```bash
python -c "
from core.bot import TradingBot
from core.strategies import SMACrossover
bot = TradingBot('BTC/USDT', SMACrossover(), capital=10000)
stats = bot.run(max_iterations=100)
print(stats)
"
```

---

---

# 15. Flux Complet d'un Trade

Voici **exactement** ce qui se passe, de A à Z, quand le bot détecte une opportunité :

```
┌─────────────────────────────────────────────────────────────┐
│  TICK N°247 — BTC/USDT                                      │
│  Prix de clôture : 67 300$                                  │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  1. data.py → fetch_candle()                                │
│     → Bougie générée : {open:67100, high:67500, close:67300}│
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  2. bot.py → _check_exits(67300)                            │
│     → Pas de position ouverte → rien à faire               │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  3. strategies.py → SMACrossover.generate()                 │
│     → SMA(10) précédente = 67 100, SMA(30) précédente = 67 200│
│     → SMA(10) actuelle   = 67 250, SMA(30) actuelle   = 67 200│
│     → Croisement détecté ! SMA rapide > SMA lente          │
│     → Retourne : Signal.BUY                                 │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  4. bot.py → _execute_signal(BUY, 67300)                    │
│                                                             │
│  indicators.py → atr() = 150$                               │
│                                                             │
│  portfolio.py → RiskManager :                               │
│    stop_loss  = 67300 - 2 × 150  = 67 000$                 │
│    take_profit = 67300 + 2 × 300 = 67 900$                 │
│    position_size = (10000 × 1%) / 300 = 0.333 BTC          │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  5. portfolio.py → Portfolio.open_position()                │
│     → cash : 10 000$ → 10 000 - (0.333 × 67 300) = -12$   │
│       (le coût = 22 410$, on a 10 000$ : mode simulation)  │
│     → positions["BTC/USDT"] = Position(qty=0.333, ...)     │
└─────────────────────────────────────────────────────────────┘
         │
         ├─────────────────────────────────────────────────┐
         ▼                                                 ▼
┌──────────────────────────┐          ┌──────────────────────────────┐
│  exchange.py             │          │  notifications.py            │
│  create_market_order(    │          │  send_discord_message(       │
│    "BTC/USDT", "buy",    │          │    "🟢 NOUVELLE POSITION..."  │
│    0.333                 │          │  )                           │
│  )                       │          │  → Message envoyé sur Discord│
│  → [Simulation] log      │          └──────────────────────────────┘
└──────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  6. web_app.py → manager.broadcast(state)                   │
│     → Envoi WebSocket vers tous les navigateurs connectés   │
│     → Dashboard mis à jour en temps réel :                  │
│        - Nouveau point sur le graphique                     │
│        - Position affichée dans le tableau                  │
│        - Equity mis à jour                                  │
└─────────────────────────────────────────────────────────────┘
         │
         ▼  [ ... 150 bougies plus tard ... ]
         │
┌─────────────────────────────────────────────────────────────┐
│  TICK N°397 — Prix actuel : 67 900$  (= Take-Profit)       │
│                                                             │
│  bot.py → _check_exits(67900)                              │
│    → price >= pos.tp → close_position("take-profit")       │
│    → PnL = (67900 - 67300) × 0.333 = +199.80$             │
│    → closed_trades.append({pnl: +199.80, reason: "tp"})   │
│    → Discord : "✅ POSITION FERMÉE | PnL: +199.80$"        │
└─────────────────────────────────────────────────────────────┘
```

---

---

*⚠️ Avertissement : Ce projet est développé à des fins éducatives et de démonstration technique. Ne pas utiliser avec de l'argent réel sans tests approfondis en paper trading (testnet). Les marchés financiers comportent des risques de perte en capital.*

---

**Fichiers du projet :** `data.py` · `indicators.py` · `strategies.py` · `portfolio.py` · `bot.py` · `exchange.py` · `notifications.py` · `ai_model.py` · `web_app.py` · `config.py`
