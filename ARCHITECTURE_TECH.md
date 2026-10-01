# Architecture et Stack Technique du Projet de Trading Bot

Ce document décrit en détail l'architecture logicielle ainsi que la stack technique sous-jacente du bot de trading automatisé. Le projet repose sur une architecture modulaire séparant strictement la logique financière algorithmique (le "Core") de l'interface utilisateur web et du serveur.

---

## 1. Stack Technique Globale

Le projet s'appuie sur des technologies modernes favorisant la haute performance, le temps réel et l'asynchronisme.

### **Backend (Python)**
*   **Langage :** Python 3.10+ (pour ses capacités avancées en typage dynamique et asynchronisme).
*   **Framework Web :** **FastAPI** (Très performant, conçu pour des APIs rapides).
*   **Serveur ASGI :** **Uvicorn** (pour exécuter l'application FastAPI en production locale).
*   **Communication Temps Réel :** **WebSockets** natifs (FastAPI.websockets) pour streamer les données de bourse au client.
*   **Machine Learning (Optionnel) :** `scikit-learn`, `xgboost` pour les stratégies propulsées par IA.
*   **Connexions Exchanges (Optionnel) :** `ccxt` pour interagir avec des APIs boursières (Binance, Kraken).

### **Frontend (Navigateur)**
*   **Structure HTML :** HTML5 (fichier `index.html` unique).
*   **Logique Interactive :** Vanilla JavaScript (`app.js`).
*   **Style Visuel :** Vanilla CSS3 (`style.css`), utilisant des techniques modernes de *Glassmorphism* et un design system "Dark Green" orienté finance.
*   **Visualisation de Données :** **Plotly.js** (création de graphiques de chandeliers en temps réel).

---

## 2. Architecture Globale du Système

Le système est conçu autour du patron **Client-Serveur Asynchrone basé sur les Événements**.

1.  **Boucle Principale en Tâche de Fond (Background Task) :** Le moteur de trading tourne en permanence à intervalle régulier (1 seconde par défaut en simulation) au sein du serveur via une boucle asynchrone (`asyncio.create_task`).
2.  **Streaming par WebSockets :** À chaque tick (nouvelle bougie ou nouveau trade exécuté), le backend "pousse" le nouvel état du portefeuille et du marché vers le frontend en format JSON.
3.  **Commandes Bidirectionnelles :** Le Frontend peut envoyer des directives en direct via la WebSocket pour modifier le comportement du système sans l'arrêter (ex: Changer de stratégie, Forcer ou fermer un Trade, Ajuster les règles de risque).

---

## 3. Architecture Modulaire Interne (Dossier `/core`)

La logique métier est contenue exclusivement dans le dossier `core`. Elle obéit au principe de responsabilité unique (SRP - Single Responsibility Principle).

*   **`bot.py` (L'Orchestrateur) :**
    Contient la classe `TradingBot`. C'est le chef d'orchestre. Il initialise tous les sous-composants (Portfolio, Data, Strategy) et définit la méthode centrale `tick()` qui avance le temps d'un cycle de marché.

*   **`data.py` (Couche Données) :**
    Simule (Random Walk) ou récupère les vraies données de marché (OHLCV : Open, High, Low, Close, Volume). Le bot de trading y est agnostic : il ne sait pas d'où viennent les données.

*   **`indicators.py` (Couche Mathématique) :**
    Implémentation pure (`@staticmethod`) des calculs mathématiques : Moyennes Mobiles (SMA/EMA), RSI, MACD, Bandes de Bollinger et Volatilité (ATR). Ni état ni contexte.

*   **`strategies.py` & `ai_model.py` (Le Cerveau Décisionnel) :**
    Les algorithmes qui reçoivent l'historique de prix et renvoient un *Signal* (`BUY`, `SELL`, `HOLD`).
    Particularité : Utilisation du modèle `EnsembleStrategy` (une intelligence collective agrégeant les points de vue de plusieurs sous-stratégies) et d'une intégration d'Intelligence Artificielle (`MLAIStrategy`).

*   **`portfolio.py` (Gestion des Risques & Capital) :**
    Dédié à l'évaluation du risque. Gère la caisse (Cash), garde un registre des trades ouverts et fermés (`positions`), et exécute les fonctions du **Risk Management** (Taille de lot, vérification de drawdown, Stop-Loss / Take-Profit). Un module `Backtester` s'y trouve également.

*   **`exchange.py` (Le Pont d'Exécution) :**
    Le traducteur physique qui prend la commande logicielle et l'envoie sur un vrai marché financier via les clés API (ex: Binance Testnet).

*   **`notifications.py` (Alertes) :**
    Connexions à l'extérieur pour avertir l'utilisateur d'un trade sur d'autres plateformes via webhooks (Discord / Telegram).

---

## 4. Flux d'Exécution Typique (Data Pipeline)

Voici ce qu'il se passe lors d'une itération temporelle standard (Tick) :

1.  **Génération de l'Événement :** `run_bot_loop()` appelle `bot.tick()`.
2.  **Mise à jour des Prix :** `bot.data` crache une nouvelle bougie (Candle).
3.  **Surveillance active (Portfolio) :** On met à jour l'évolution des positions non-clôturées en fonction du nouveau prix. Si un Stop-Loss est franchi, la position est liquidée.
4.  **Analyse de Marché (Strategy) :** On fournit les dernières bougies à la `Strategy` active. Celle-ci fait ses propres appels à `indicators.py` pour valider ou rejeter un signal.
5.  **Prise de Décision :** Si le signal est un *BUY*, le bot interroge le `Portfolio` pour qu'il déduise la part de risque acceptable, puis exécute l'achat virtuel ou réel.
6.  **Broadcast (WebSocket) :** Une image complète (Snapshot) du Portefeuille et de la dernière bougie est packagée en JSON et envoyée à tous les clients WebSockets connectés.
7.  **Affichage de l'Interface UI :** Le Javascript reçoit le paquet WebSocket, met à jour le PnL, ajoute la bougie sur le graphique Plotly et synchronise l'historique des transactions.
