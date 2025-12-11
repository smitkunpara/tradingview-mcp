"""
Centralized Configuration Manager.
Loads environment variables once and allows runtime updates.
"""
import os
from dotenv import load_dotenv, set_key

# Load .env file immediately
load_dotenv()

class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initial load of configuration"""
        self.TRADINGVIEW_COOKIE = os.getenv("TRADINGVIEW_COOKIE", "")
        self.TRADINGVIEW_URL = os.getenv("TRADINGVIEW_URL", "https://in.tradingview.com/chart/")
        self.USER_AGENT = os.getenv("TRADINGVIEW_USER_AGENT", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        self.ENV_FILE_PATH = os.path.join(os.getcwd(), ".env")
        
        # --- NEW SECURITY KEYS ---
        # Default keys provided for safety if env vars missing
        self.ADMIN_API_KEY = os.getenv("TV_ADMIN_KEY", "admin-secret-123") 
        self.CLIENT_API_KEY = os.getenv("TV_CLIENT_KEY", "client-secret-123")

    def update_cookie(self, new_cookie_string: str):
        """Updates cookie in memory and tries to save to .env file"""
        # 1. Update In-Memory (Immediate effect for all modules)
        self.TRADINGVIEW_COOKIE = new_cookie_string
        
        # 2. Update Environment Variable (For libraries checking os.environ)
        os.environ["TRADINGVIEW_COOKIE"] = new_cookie_string

        # 3. Persist to file (Works in Localhost, Ignored in Vercel/Read-only envs)
        try:
            if os.path.exists(self.ENV_FILE_PATH):
                set_key(self.ENV_FILE_PATH, "TRADINGVIEW_COOKIE", new_cookie_string)
                print(f"✅ Updated .env file locally.")
            else:
                print("⚠️ .env file not found, skipping persistence.")
        except Exception as e:
            print(f"⚠️ Could not write to .env (expected on Vercel/ReadOnly): {e}")

# Global instance
settings = Settings()