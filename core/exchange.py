import logging

log = logging.getLogger(__name__)

class ExchangeManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ExchangeManager, cls).__new__(cls)
            cls._instance.exchange = None
        return cls._instance

    def initialize(self, api_key: str, api_secret: str, testnet: bool = True):
        try:
            import ccxt
            
            
            self.exchange = ccxt.bybit({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
            })
            
            if testnet:
                self.exchange.set_sandbox_mode(True)
                
            
            self.exchange.fetch_balance()
            log.info(f"Connexion CCXT (Bybit) {'TESTNET' if testnet else 'LIVE'} réussie !")
            return True
            
        except ImportError:
            log.error("Module CCXT non installé. Impossible d'initialiser le trading réel.")
            return False
        except Exception as e:
            log.error(f"Erreur d'initialisation CCXT : {e}")
            self.exchange = None
            return False

    def create_market_order(self, symbol: str, side: str, amount: float):
        if not self.exchange:
            log.warning(f"[Simulation CCXT] Ordre {side} sur {symbol} de {amount}")
            return True
        try:
            order = self.exchange.create_market_order(symbol, side, amount)
            log.info(f"Ordre Réel Exécuté: {order}")
            return order
        except Exception as e:
            log.error(f"Echec de l'ordre réel: {e}")
            return False


exchange_client = ExchangeManager()
