"""
gui_matplotlib_fixed.py - Version avec graphiques Matplotlib qui fonctionne
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import random
from datetime import datetime

# Import de Matplotlib
import matplotlib
matplotlib.use('TkAgg')  # Important pour l'intégration Tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from bot import (
    MarketData, Indicators, Signal,
    SMACrossover, RSIStrategy, MACDStrategy,
    BollingerStrategy, EnsembleStrategy,
    TradingBot
)


class TradingBotGUIWithCharts:
    """Interface graphique avec graphiques Matplotlib fonctionnels"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Trading Bot - Interface Graphique")
        self.root.geometry("1400x900")
        
        # Variables
        self.bot_thread = None
        self.running = False
        self.demo_mode = True  
        
        # Couleurs
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'buy': '#00ff88',
            'sell': '#ff4444'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        
        self.create_widgets()
        
        
        self.start_demo()
        
    def create_widgets(self):
        """Crée tous les widgets"""
        
       
        left_frame = ttk.Frame(self.root)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        
        control_frame = ttk.LabelFrame(left_frame, text="🎮 Contrôle", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="📊 Générer données démo", 
                  command=self.start_demo).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="🔄 Mettre à jour graphique", 
                  command=self.update_charts).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="▶️ Démarrer Bot", 
                  command=self.start_bot).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="⏹️ Arrêter Bot", 
                  command=self.stop_bot).pack(fill=tk.X, pady=5)
        
        
        stats_frame = ttk.LabelFrame(left_frame, text="📈 Statistiques", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=15, 
                                                     bg='#2b2b2b', fg='#ffffff')
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        
        right_frame = ttk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        
        self.create_charts(right_frame)
        
        
        log_frame = ttk.LabelFrame(right_frame, text="📝 Logs", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8,
                                                   bg='#2b2b2b', fg='#ffffff')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def create_charts(self, parent):
        """Crée les graphiques Matplotlib"""
        
        
        charts_frame = ttk.LabelFrame(parent, text="📊 Analyse Technique", padding=10)
        charts_frame.pack(fill=tk.BOTH, expand=True)
        
        
        self.fig = Figure(figsize=(10, 6), facecolor=self.colors['bg'], dpi=100)
        self.fig.subplots_adjust(hspace=0.3, left=0.1, right=0.95, top=0.95, bottom=0.08)
        
        
        self.ax_price = self.fig.add_subplot(211)
        self.ax_price.set_facecolor('#2b2b2b')
        self.ax_price.set_title("Prix et Moyennes Mobiles", color='white', fontsize=12)
        self.ax_price.tick_params(colors='white')
        self.ax_price.grid(True, alpha=0.3, color='gray')
        
        
        self.ax_rsi = self.fig.add_subplot(212)
        self.ax_rsi.set_facecolor('#2b2b2b')
        self.ax_rsi.set_title("RSI (Relative Strength Index)", color='white', fontsize=12)
        self.ax_rsi.tick_params(colors='white')
        self.ax_rsi.grid(True, alpha=0.3, color='gray')
        self.ax_rsi.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='Sur-achat')
        self.ax_rsi.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='Sur-vente')
        
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=charts_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def generate_demo_data(self):
        """Génère des données de démonstration"""
        
        prices = [100]
        for _ in range(199):
            change = random.gauss(0, 0.015)
            prices.append(prices[-1] * (1 + change))
        
        
        sma20 = []
        sma50 = []
        rsi = []
        
        for i in range(len(prices)):
            if i >= 19:
                sma20.append(sum(prices[i-19:i+1]) / 20)
            else:
                sma20.append(None)
            
            if i >= 49:
                sma50.append(sum(prices[i-49:i+1]) / 50)
            else:
                sma50.append(None)
            
            if i >= 20:
                rsi_val = self.calculate_rsi(prices[:i+1], 14)
                rsi.append(rsi_val)
            else:
                rsi.append(None)
        
        return prices, sma20, sma50, rsi
    
    def calculate_rsi(self, prices, period=14):
        """Calcule le RSI"""
        if len(prices) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-diff)
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def update_charts(self):
        """Met à jour les graphiques"""
        
        if self.demo_mode or not hasattr(self, 'bot'):
            prices, sma20, sma50, rsi = self.generate_demo_data()
        else:
            
            closes = self.bot.data.closes()
            prices = closes[-200:] if len(closes) > 200 else closes
            sma20 = []
            sma50 = []
            rsi = []
            
            for i in range(len(prices)):
                if i >= 19:
                    sma20.append(sum(prices[i-19:i+1]) / 20)
                else:
                    sma20.append(None)
                
                if i >= 49:
                    sma50.append(sum(prices[i-49:i+1]) / 50)
                else:
                    sma50.append(None)
                
                if i >= 20:
                    rsi_val = self.calculate_rsi(prices[:i+1], 14)
                    rsi.append(rsi_val)
                else:
                    rsi.append(None)
        
        
        self.ax_price.clear()
        self.ax_rsi.clear()
        
        
        self.ax_price.set_facecolor('#2b2b2b')
        self.ax_price.set_title("Prix et Moyennes Mobiles", color='white', fontsize=12)
        self.ax_price.tick_params(colors='white')
        self.ax_price.grid(True, alpha=0.3, color='gray')
        
        self.ax_rsi.set_facecolor('#2b2b2b')
        self.ax_rsi.set_title("RSI (Relative Strength Index)", color='white', fontsize=12)
        self.ax_rsi.tick_params(colors='white')
        self.ax_rsi.grid(True, alpha=0.3, color='gray')
        self.ax_rsi.axhline(y=70, color='red', linestyle='--', alpha=0.5, linewidth=1)
        self.ax_rsi.axhline(y=30, color='green', linestyle='--', alpha=0.5, linewidth=1)
        
        
        self.ax_price.plot(prices, color='cyan', linewidth=1.5, label='Prix')
        
        
        valid_sma20 = [(i, v) for i, v in enumerate(sma20) if v is not None]
        valid_sma50 = [(i, v) for i, v in enumerate(sma50) if v is not None]
        
        if valid_sma20:
            x, y = zip(*valid_sma20)
            self.ax_price.plot(x, y, color='yellow', linewidth=1, label='SMA 20', alpha=0.8)
        
        if valid_sma50:
            x, y = zip(*valid_sma50)
            self.ax_price.plot(x, y, color='orange', linewidth=1, label='SMA 50', alpha=0.8)
        
        
        valid_rsi = [(i, v) for i, v in enumerate(rsi) if v is not None]
        if valid_rsi:
            x, y = zip(*valid_rsi)
            self.ax_rsi.plot(x, y, color='magenta', linewidth=1.5, label='RSI')
        
        
        self.ax_price.legend(loc='upper left', facecolor='#2b2b2b', labelcolor='white')
        self.ax_rsi.legend(loc='upper left', facecolor='#2b2b2b', labelcolor='white')
        
       
        if valid_rsi:
            x_vals = list(range(len(rsi)))
            self.ax_rsi.fill_between(x_vals, 30, 70, alpha=0.1, color='green')
        
        
        self.canvas.draw()
        
        
        self.update_stats(prices)
        
        self.log("✅ Graphiques mis à jour")
        
    def update_stats(self, prices):
        """Met à jour les statistiques"""
        if not prices:
            return
        
        current_price = prices[-1]
        price_change = ((prices[-1] - prices[0]) / prices[0]) * 100 if len(prices) > 1 else 0
        
        
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        volatility = (sum([r**2 for r in returns[-20:]]) / 20) ** 0.5 * (252 ** 0.5) if returns else 0
        
        
        current_rsi = self.calculate_rsi(prices, 14) if len(prices) > 14 else 50
        
        stats = f"""
{'='*40}
📊 STATISTIQUES DU MARCHÉ
{'='*40}

💰 Prix actuel: {current_price:.2f}
📈 Variation totale: {price_change:+.2f}%
📉 Volatilité (annualisée): {volatility:.2%}
🎯 RSI (14): {current_rsi:.1f}

📈 Derniers prix:
{', '.join([f'{p:.2f}' for p in prices[-10:]])}

{'='*40}
        """
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, stats)
        
    def start_demo(self):
        """Démarre le mode démonstration"""
        self.demo_mode = True
        self.log("🎬 Mode démo démarré - Génération de données aléatoires")
        self.update_charts()
        
       
        if hasattr(self, 'animation_job'):
            self.root.after_cancel(self.animation_job)
        self.animate_demo()
        
    def animate_demo(self):
        """Animation des graphiques en mode démo"""
        if self.demo_mode:
            self.update_charts()
            self.animation_job = self.root.after(3000, self.animate_demo)
        
    def start_bot(self):
        """Démarre le bot réel"""
        self.demo_mode = False
        
       
        strategy = EnsembleStrategy([
            SMACrossover(10, 30),
            RSIStrategy(70, 30),
            MACDStrategy(),
            BollingerStrategy()
        ])
        
        
        self.bot = TradingBot(
            symbol="BTC/USDT",
            strategy=strategy,
            capital=10000,
            interval_sec=2
        )
        
        
        self.running = True
        self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
        self.bot_thread.start()
        
        self.log("🤖 Bot démarré en mode réel")
        
        
        self.update_bot_charts()
        
    def run_bot(self):
        """Exécute le bot"""
        try:
           
            for _ in range(50):
                if not self.running:
                    break
                candle = self.bot.data.fetch_candle()
                
                import time
                time.sleep(2)
        except Exception as e:
            self.log(f"❌ Erreur bot: {e}")
        finally:
            self.running = False
            
    def update_bot_charts(self):
        """Met à jour les graphiques avec les données du bot"""
        if not self.demo_mode and hasattr(self, 'bot') and self.running:
            self.update_charts()
            self.root.after(2000, self.update_bot_charts)
        
    def stop_bot(self):
        """Arrête le bot"""
        self.running = False
        self.demo_mode = True
        self.log("⏹️ Bot arrêté, retour en mode démo")
        self.animate_demo()
        
    def log(self, message):
        """Ajoute un message dans les logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
    def on_closing(self):
        """Fermeture propre"""
        if hasattr(self, 'animation_job'):
            self.root.after_cancel(self.animation_job)
        self.running = False
        self.root.destroy()



if __name__ == "__main__":
    root = tk.Tk()
    app = TradingBotGUIWithCharts(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()