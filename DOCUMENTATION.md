# 📚 Documentation Complète : Trading Bot & Web Dashboard

## 🎯 Vue d'ensemble du Projet
Ce projet est une plateforme de trading automatisée complète construite en Python. Il a été récemment modernisé pour passer d'un script monolithique (fonctionnant dans le terminal local ou Tkinter) vers une architecture hautement modulaire couplée à un **Dashboard Premium en Temps Réel** accessible via le navigateur.

L'objectif de cette architecture est la flexibilité : pouvoir brancher, créer ou débrancher des stratégies sans modifier le moteur central, et pouvoir gérer visuellement le risque de manière professionnelle.

---

## 🏗 L'Architecture Core (`/core`)
Tout l'intelligence financière du Bot se trouve dans le sous-dossier `core/`. Cette séparation stricte permet au code de ne jamais s'emmêler entre la logique mathématique (trading) et l'interface (navigateur).

### 1. `core/data.py` (Moteur de Données)
- **Rôle :** Simule actuellement les données des marchés monétaires ("MarketData").
- **Fonctionnement :** Produit au hasard des bougies financières (Open, High, Low, Close, Volume) selon la méthode du *Random Walk* (marche aléatoire). À chaque *tick* de la boucle temporelle, il recrée artificiellement la volatilité.
- **Évolution :** Dans le futur, c'est ce fichier qui devra être modifié pour récupérer les données de l'API de Binance ou Kraken en remplaçant la logique aléatoire par des requêtes d'API.

### 2. `core/indicators.py` (Outils d'Analyse Mathématique)
- **Rôle :** Boîte à outils purement statique regroupant les formules de finance quantitative. Rien d'autre que du calcul.
- **Contenu :**
    - `SMA` (Simple Moving Average)
    - `RSI` (Relative Strength Index)
    - `MACD` (Moving Average Convergence Divergence)
    - `Bollinger Bands`
    - `ATR` (Average True Range) : Essentiel pour calculer dynamiquement la volatilité et placer nos *Stop-Loss* de manière espacée.

### 3. `core/strategies.py` (Cerveau Décisionnel)
- **Rôle :** Définit les critères pour déclencher les achats (`BUY`), les ventes (`SELL`) ou repousser (`HOLD`).
- **Contenu :** Chaque logique possède sa propre classe. À la fin, la magie opère via l'`EnsembleStrategy` : un algorithme qui exécute plusieurs stratégies en même temps, compte leurs votes, et sort une décision par consensus démocratique (idéal en vrai marché).

### 4. `core/portfolio.py` (Gestion du Portefeuille et des Risques)
- **Rôle :** C'est le caissier et la tour de contrôle. Il traque le capital, prend et coupe les positions et calcule les taux de réussite.
- **Le « RiskManager » :** Ne laisse jamais le hasard ruiner votre argent ! Il décide de la *taille exacte* du lot (Qty) lors d'un trade pour qu'un Stop-Loss écrasé ne dépasse jamais votre `max_risk_pct` (ex: 1% du sac de cash total). Il protège également en coupant le bot via une mise sous silence (Emergency block) si un seuil de **Drawdown absolu** est atteint.

### 5. `core/bot.py` (Le Mouvement d'Horlogerie)
- **Rôle :** Le maître d'orchestre (`TradingBot`).
- **Fonctionnement :** Son unique job est d'attraper les dernières données de `data.py`, vérifier que le portefeuille n'est pas en banqueroute via `portfolio.py`, passer la bougie à `strategies.py` et si un signal d'achat tombe, déclencher l'ouverture du ticket. Cette boucle s'accomplit sans fin, seconde après seconde (la fonction `tick()`).

---

## 💻 Le Dashboard Web (`web_app.py` & `/static`)
Le coeur technologique de la modernisation !

### Comment ça marche ?
1. **Le Backend (`web_app.py`) :** Utilise `FastAPI`. Il lance le `TradingBot` en mode tâche de fond (background task). Il établit un pont bidirectionnel extrêmement véloce appelé **WebSocket** (`/ws`). C'est par là qu'il propulse à la fréquence de 1 message par seconde le résultat du bot.
2. **Le Frontend (`static/`) :** C'est ce que voit l'utilisateur. 
    - Le `layout` est un design Premium (Dark Green Glassmorphism).
    - `app.js` écoute la WebSocket. À chaque milliseconde qu'une bougie arrive, le Javascript donne l'ordre à la bibliothèque graphique poussée (ici `Plotly.js`) de repeindre les chandeliers japonais à l'écran. 

---

## 🚀 Le Guide d'Utilisation

### Lancement
Pour démarrer tout ce système sur votre machine, ouvrez votre Terminal (PowerShell), et exécutez strictement ceci :

```bash
uvicorn web_app:app --host 127.0.0.1 --port 8000
```

Ensuite, rendez-vous dans le navigateur et tapez : **http://127.0.0.1:8000**

👉 L'application chargera les composants de design et vous pouvez cliquer sur **Démarrer Bot**. Vous serez témoin de l'actualisation dynamique du PnL.

---

## 🔧 Comment revenir à une Stratégie Sérieuse / Complexe ?

Le Dashboard utilise actuellement une stratégie factice très agressive paramétrée exprès pour déclencher des achats visuels (`SMACrossover(2, 4)`). Ce n'est qu'à des fins de "Test" visuel de la plateforme.

Lorsque vous voudrez déployer ce Bot sur un projet sérieux avec l'algorithme "Machine Consensus" (`EnsembleStrategy`), ouvrez le fichier `web_app.py` et modifiez les **lignes 14/15** ainsi :

**A) Remplacer ce bloc de démonstration actuel :**
```python
# Setup strategy and Bot
strategy = SMACrossover(2, 4) # Stratégie hyper-réactive pour observation
bot = TradingBot(symbol="BTC/USDT", strategy=strategy, capital=10000, interval_sec=1)
```

**B) Vers l'Arme Lourde de Production originelle :**
```python
# Setup strategy and Bot
strategy = EnsembleStrategy([
    SMACrossover(10, 30),
    RSIStrategy(70, 30),
    MACDStrategy(),
    BollingerStrategy()
])
bot = TradingBot(symbol="BTC/USDT", strategy=strategy, capital=10000, interval_sec=1) # Vous pouvez remplacer random sec par sec
``` 

*Une fois remplacé, sauvegardez et redémarrez votre commande uvicorn.*
