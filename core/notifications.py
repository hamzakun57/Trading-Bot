import requests
import logging

log = logging.getLogger(__name__)

class NotificationManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotificationManager, cls).__new__(cls)
            cls._instance.discord_webhook_url = ""
        return cls._instance

    def set_discord_webhook(self, url: str):
        self.discord_webhook_url = url
        log.info(f"Discord Webhook configuré: {url[:15]}...")

    def send_discord_message(self, message: str, color: int = 0x00E676):
        if not self.discord_webhook_url:
            return
        
        payload = {
            "embeds": [
                {
                    "title": "🤖 CryptoBot Alert",
                    "description": message,
                    "color": color
                }
            ]
        }
        
        try:
            requests.post(self.discord_webhook_url, json=payload, timeout=5)
        except Exception as e:
            log.error(f"Erreur envoi Discord: {e}")


notifier = NotificationManager()
