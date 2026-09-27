import os
from dataclasses import dataclass

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    OXAPAY_API_KEY: str = os.getenv("OXAPAY_API_KEY", "YOUR_OXAPAY_API_KEY")
    OXAPAY_MERCHANT_ID: str = os.getenv("OXAPAY_MERCHANT_ID", "YOUR_MERCHANT_ID")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "123456789"))
    
    # Payment rates
    STARS_TO_POINTS: float = 1.95  # 100 stars = 195 points
    CRYPTO_TO_POINTS: float = 100  # 1 USD = 100 points
    POINTS_TO_USD: float = 0.01    # 100 points = 1 USD
    
    # Wallet addresses for manual payment
    TON_WALLET: str = os.getenv("TON_WALLET", "UQD...")
    USDT_TRC20_WALLET: str = os.getenv("USDT_TRC20_WALLET", "T...")
    USDT_ERC20_WALLET: str = os.getenv("USDT_ERC20_WALLET", "0x...")

config = Config()
