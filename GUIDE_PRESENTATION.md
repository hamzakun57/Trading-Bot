# 🎤 Guide de Présentation — CryptoBot Trading Algorithmique

> **Durée estimée :** 15–20 minutes  
> **Structure :** 6 parties + démo live  
> **Outils :** Présentation HTML + Dashboard `http://localhost:8000`

---

## ✅ Checklist AVANT de commencer

| # | Vérification |
|---|-------------|
| 1 | `python web_app.py` tourne sans erreur dans le terminal |
| 2 | `http://localhost:8000` s'ouvre dans Chrome/Edge |
| 3 | La présentation HTML est prête : `http://localhost:8000/static/presentation.html` |
| 4 | Mode simulation activé (`use_binance = False` dans `web_app.py`) |
| 5 | Capital : 10 000$ · Stratégie par défaut : SMACrossover |
| 6 | Deux onglets ouverts : **Slide 1** et **Dashboard** |

---

## 🗂️ Ordre des onglets recommandé

```
Onglet 1 → Présentation HTML  (slides de présentation)
Onglet 2 → http://localhost:8000  (démo live du bot)
```

Ferme tout le reste pour rester concentré.

---

---

## PARTIE 1 — Introduction (2 min)

> 🖥️ *Ouvrir la présentation HTML — Slide 1*

### Ce que tu dis :

> *"Je vais vous présenter un bot de trading algorithmique que j'ai développé entièrement en Python.*
> *Il analyse les marchés crypto en temps réel, prend des décisions d'achat/vente automatiquement,*
> *et affiche tout ça dans un dashboard web moderne."*

### Points à mentionner :

- **Stack technique :** Python 3.11 · FastAPI · WebSocket · HTML/CSS/JS
- **Architecture modulaire :** 9 fichiers Python organisés en couches
- Tu as conçu **l'architecture et la logique de trading de A à Z**

---

---

## PARTIE 2 — C'est quoi le Trading ? (3 min)

> 🖥️ *Slide 2 — "Qu'est-ce que le Trading ?"*

### Ce que tu dis :

> *"Avant de plonger dans le code, quelques notions de base pour comprendre ce que fait le bot."*

### Points à expliquer :

**📈 Le principe fondamental**
> *"Le trading, c'est acheter un actif à un prix donné et le revendre plus cher pour faire un profit.*
> *Ce profit s'appelle le PnL — Profit and Loss."*

**💱 Une paire de trading**
> *"Sur les cryptos, on travaille avec des paires comme BTC/USDT.*
> *Ça veut dire : combien de dollars vaut 1 Bitcoin.*
> *On achète du BTC avec des dollars, et on revend pour récupérer plus de dollars."*

**🕯️ Une bougie (Candlestick)**
> *"Chaque bougie représente l'évolution du prix sur une période.*
> *Elle contient 4 valeurs : Open, High, Low, Close — et le Volume échangé.*
> *C'est la donnée de base sur laquelle tout le bot travaille."*

**🟢🔴 Long vs Short**
> *"LONG = tu paries que le prix va monter → tu achètes.*
> *SHORT = tu paries que le prix va baisser → tu vends ce que tu n'as pas encore.*
> *Notre bot utilise uniquement des positions LONG pour rester simple."*

**⚡ Algorithmique vs Manuel**
> *"Un humain surveille les écrans et clique manuellement.*
> *Un bot algorithmique, lui, analyse les données en continu, sans émotion, 24h/24.*
> *Il ne panique pas, ne se laisse pas emporter par la peur ou l'euphorie."*

---

---

## PARTIE 3 — Les Indicateurs Techniques (2 min)

> 🖥️ *Slide 3 — "Indicateurs Techniques"*

### Ce que tu dis :

> *"Le bot ne trade pas au hasard.*
> *Il calcule des indicateurs mathématiques sur l'historique des prix pour détecter des opportunités."*

### Les 4 indicateurs du projet :

**〰️ SMA / EMA (Moyenne Mobile)**
> *"Lisse les prix pour dégager une tendance.*
> *Quand la moyenne rapide croise la moyenne lente vers le haut → signal d'achat BUY.*
> *Exemple : SMA(10) dépasse SMA(30) → le marché est en tendance haussière."*

**📉 RSI (Relative Strength Index)**
> *"Mesure si le marché est 'épuisé'.*
> *RSI sous 30 = le prix a trop baissé → survente → opportunité d'achat.*
> *RSI au-dessus de 70 = le prix a trop monté → surachat → signal de vente."*

**🌊 MACD**
> *"Mesure la dynamique de tendance via le croisement de deux moyennes exponentielles.*
> *Quand la ligne MACD passe au-dessus de sa ligne signal → momentum haussier → BUY."*

**📦 ATR (Average True Range)**
> *"Mesure la volatilité du marché.*
> *C'est L'indicateur clé du bot : il sert à calculer automatiquement le Stop-Loss.*
> *Plus le marché est volatile, plus le stop est large."*

---

---

## PARTIE 4 — La Gestion du Risque (2–3 min)

> 🖥️ *Slide 4 — "Gestion du Risque"*  
> ⚠️ **C'est le slide le plus important — insiste dessus**

### Ce que tu dis :

> *"Un bon bot ne cherche pas juste à gagner — il cherche surtout à NE PAS PERDRE.*
> *La règle d'or en trading : protéger le capital AVANT de chercher des profits.*
> *Pour chaque trade, le RiskManager calcule automatiquement 3 choses."*

### Les 3 piliers à expliquer :

**1. Stop-Loss (SL)**
> *"Si le prix descend en dessous d'un certain seuil → on coupe la perte automatiquement.*
> *Formule : prix d'entrée moins 2 fois l'ATR.*
> *Exemple : BTC à 67 300$, ATR = 150$ → Stop-Loss à 67 000$.*
> *Si le prix tombe à 67 000$, le bot vend immédiatement pour éviter une perte plus grande."*

**2. Take-Profit (TP)**
> *"Si le prix atteint l'objectif → on verrouille le profit automatiquement.*
> *Formule : prix d'entrée plus 4 fois l'ATR (ratio risque/récompense de 1:2).*
> *Exemple : BTC à 67 300$ → Take-Profit à 67 900$.*
> *On risque 300$ pour gagner 600$. C'est mathématiquement rentable."*

**3. Position Size (taille de position)**
> *"On ne mise jamais tout son capital.*
> *Le bot risque exactement 1% du capital par trade.*
> *Exemple : capital 10 000$ → risque max par trade = 100$.*
> *Distance au stop = 300$ → quantité = 100/300 = 0.33 BTC.*
> *Ainsi, même en perdant 10 trades de suite, le capital reste intact à 90%."*

**4. Max Drawdown**
> *"Si les pertes cumulées dépassent 15% du capital total → le bot s'arrête complètement.*
> *C'est un filet de sécurité global."*

---

---

## PARTIE 5 — L'Architecture du Projet (3 min)

> 🖥️ *Slide 6 → Slide 7 — "Modules" puis "Flux d'un Trade"*

### Ce que tu dis (slide 6) :

> *"Techniquement, le projet est structuré en couches logiques.*
> *Chaque fichier a une responsabilité unique — c'est ce qu'on appelle la séparation des préoccupations."*

### Les 4 couches :

```
🌐 Présentation   → web_app.py + static/index.html
🤖 Bot            → core/bot.py + core/data.py
📊 Analyse        → core/indicators.py + core/strategies.py + core/ai_model.py
💼 Exécution      → core/portfolio.py + core/exchange.py + core/notifications.py
```

### Ce que tu dis (slide 7 — Flux d'un trade) :

> *"Voici ce qui se passe à chaque seconde quand le bot tourne :"*

```
📡 data.py        → Récupère une nouvelle bougie (prix OHLCV)
        ↓
📐 indicators.py  → Calcule l'ATR et les moyennes mobiles
        ↓
🧠 strategies.py  → Analyse et génère un signal : BUY / SELL / HOLD
        ↓
🛡️ portfolio.py   → Calcule Stop-Loss, Take-Profit, quantité à acheter
        ↓
💰 Position       → Ouverte, le cash est déduit du portefeuille
        ↓
🏦 exchange.py    → Ordre envoyé à Bybit (ou simulé si pas de clé API)
        ↓
🔔 notifications  → Alerte Discord envoyée avec les détails du trade
        ↓
🌐 web_app.py     → État diffusé via WebSocket → Dashboard mis à jour
```

### Point fort à mentionner :

> *"Deux modules utilisent le pattern Singleton : `exchange_client` et `notifier`.*
> *Ça veut dire qu'il n'existe qu'une seule instance de chacun dans tout le programme,*
> *configurée une fois depuis les settings du dashboard, accessible partout."*

> *"La communication entre le bot et le dashboard se fait via WebSocket —*
> *la page se met à jour en temps réel sans jamais se rafraîchir."*

---

---

## PARTIE 6 — Transition vers la Démo (1 min)

> 🖥️ *Slide 9 — "Prêt à trader ?"*

### Ce que tu dis :

> *"Maintenant je vais vous montrer tout ça en action.*
> *Le bot tourne en mode simulation — il génère ses propres données de marché*
> *et prend des décisions en direct. Vous allez voir les trades s'ouvrir et se fermer en temps réel."*

Puis tu passes sur l'onglet Dashboard.

---

---

## 🖥️ DÉMO LIVE — Ce que tu fais (5 min)

> *Passer sur l'onglet Dashboard : `http://localhost:8000`*

### Étapes de la démo :

1. **Montrer l'interface** — graphique, métriques, positions ouvertes
   > *"Voici le dashboard. Le graphique en chandelier évolue en temps réel.*
   > *À gauche : l'equity du portefeuille. En bas : l'historique des trades."*

2. **Cliquer sur START**
   > *"Je lance le bot. Observez le graphique — de nouvelles bougies apparaissent chaque seconde."*

3. **Attendre un trade** (quelques secondes)
   > *"Voilà — une position vient de s'ouvrir. Vous voyez le Stop-Loss, le Take-Profit, et la quantité calculée automatiquement."*

4. **Montrer les stratégies**
   > *"Je peux changer de stratégie en direct — sans redémarrer le bot.*
   > *Ici je passe en mode Ensemble : le bot vote entre 4 stratégies pour chaque décision."*

5. **Cliquer sur STOP**
   > *"Je stoppe le bot. Les statistiques finales s'affichent : Win Rate, PnL total, Profit Factor."*

6. **Ouvrir les Settings** (optionnel)
   > *"On peut configurer ici le levier, le risque par trade, et connecter une vraie clé API Bybit*
   > *ou un webhook Discord pour recevoir les alertes en temps réel."*

---

---

## 💬 Questions fréquentes — Réponses préparées

**Q : C'est quoi la différence entre mode simulation et mode réel ?**
> *"En simulation, le bot génère ses propres prix aléatoires pour tester les stratégies.*
> *En mode réel, il suffit de rentrer une clé API Bybit dans les settings — le reste est identique."*

**Q : Pourquoi Python et pas autre chose ?**
> *"Python s'impose en finance algorithmique pour ses bibliothèques (numpy, pandas, sklearn)*
> *et sa rapidité de développement. FastAPI permet un serveur async très performant."*

**Q : Le bot est-il rentable ?**
> *"En simulation oui — mais les performances passées ne garantissent pas les résultats futurs.*
> *C'est un projet éducatif pour démontrer les concepts d'architecture et de trading.*
> *Des tests rigoureux en paper trading seraient nécessaires avant tout argent réel."*

**Q : Qu'est-ce que le backtesting ?**
> *"C'est rejouer les stratégies sur des données historiques pour voir comment elles auraient performé.*
> *Le bouton Backtest dans le dashboard le fait en temps réel sur les données en mémoire."*

---

*⚠️ Rappel : Ce bot est éducatif. Ne pas utiliser avec de l'argent réel sans tests approfondis.*
