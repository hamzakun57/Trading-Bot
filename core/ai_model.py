import logging
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from core.strategies import Strategy, Signal
from core.data import MarketData

log = logging.getLogger(__name__)

class MLAIStrategy(Strategy):
    name = "AI Predictor (Random Forest)"
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        self.is_trained = False
        
    def _prepare_features(self, candles: list):
        df = pd.DataFrame(candles)
       
        df['return'] = df['close'].pct_change()
        df['sma_10'] = df['close'].rolling(10).mean()
        df['sma_30'] = df['close'].rolling(30).mean()
        
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
        df = df.dropna()
        return df

    def _train_model(self, candles: list):
        if len(candles) < 50:
            return
        log.info("Entraînement de l'IA en cours...")
        df = self._prepare_features(candles)
        
        features = ['return', 'sma_10', 'sma_30']
        if len(df) > 0:
            X = df[features]
            y = df['target']
            self.model.fit(X, y)
            self.is_trained = True
            log.info("🤖 Cerveau IA Entraîné !")

    def generate(self, data: MarketData) -> str:
        if not self.is_trained:
            self._train_model(data.candles)
            
        if not self.is_trained or len(data.candles) < 35:
            return Signal.HOLD
            
        df = self._prepare_features(data.candles[-40:])
        if len(df) == 0: 
            return Signal.HOLD
        
        last_row = df.iloc[-1]
        features = ['return', 'sma_10', 'sma_30']
        X_pred = pd.DataFrame([last_row[features]])
        
        try:
            pred = self.model.predict(X_pred)[0]
            if pred == 1:
                return Signal.BUY
            elif pred == 0:
                return Signal.SELL
        except Exception as e:
            log.error(f"Erreur de prédiction IA: {e}")
            
        return Signal.HOLD
