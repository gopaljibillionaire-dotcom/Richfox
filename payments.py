import aiohttp
from typing import Dict, Any, Optional
from config import config
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from datetime import datetime

class PaymentHandler:
    
    @staticmethod
    def get_deposit_keyboard() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="⭐ Pay with Stars", callback_data="deposit_stars")],
            [InlineKeyboardButton(text="💳 Crypto (Auto)", callback_data="deposit_crypto_auto")],
            [InlineKeyboardButton(text="💰 Crypto (Manual)", callback_data="deposit_crypto_manual")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def get_crypto_selection_keyboard() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="TON", callback_data="crypto_ton")],
            [InlineKeyboardButton(text="USDT (TRC20)", callback_data="crypto_usdt_trc20")],
            [InlineKeyboardButton(text="USDT (ERC20)", callback_data="crypto_usdt_erc20")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="wallet")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def get_withdrawal_keyboard() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="TON", callback_data="withdraw_ton")],
            [InlineKeyboardButton(text="USDT (TRC20)", callback_data="withdraw_usdt_trc20")],
            [InlineKeyboardButton(text="USDT (ERC20)", callback_data="withdraw_usdt_erc20")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="wallet")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    async def create_oxapay_payment(amount: float, currency: str = "USDT") -> Optional[Dict[str, Any]]:
        """Create OxaPay payment invoice"""
        url = "https://api.oxapay.com/merchants/request"
        
        payload = {
            "merchant": config.OXAPAY_MERCHANT_ID,
            "amount": amount,
            "currency": currency,
            "lifeTime": 30,  # 30 minutes
            "callbackUrl": "https://yourwebsite.com/callback",
            "returnUrl": "https://t.me/your_bot"
        }
        
        headers = {
            "Authorization": f"Bearer {config.OXAPAY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"OxaPay error: {e}")
        
        return None
    
    @staticmethod
    async def check_oxapay_payment(track_id: str) -> Optional[Dict[str, Any]]:
        """Check OxaPay payment status"""
        url = f"https://api.oxapay.com/merchants/inquiry"
        
        payload = {
            "merchant": config.OXAPAY_MERCHANT_ID,
            "trackId": track_id
        }
        
        headers = {
            "Authorization": f"Bearer {config.OXAPAY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"OxaPay check error: {e}")
        
        return None
    
    @staticmethod
    def get_manual_payment_info(crypto_type: str, amount: float) -> str:
        """Get manual payment information"""
        wallets = {
            "crypto_ton": config.TON_WALLET,
            "crypto_usdt_trc20": config.USDT_TRC20_WALLET,
            "crypto_usdt_erc20": config.USDT_ERC20_WALLET
        }
        
        network_names = {
            "crypto_ton": "TON",
            "crypto_usdt_trc20": "USDT (TRC20)",
            "crypto_usdt_erc20": "USDT (ERC20)"
        }
        
        wallet = wallets.get(crypto_type, "")
        network = network_names.get(crypto_type, "")
        
        text = f"💰 **Manual Payment Instructions**\n\n"
        text += f"Network: {network}\n"
        text += f"Amount: ${amount:.2f}\n\n"
        text += f"Wallet Address:\n`{wallet}`\n\n"
        text += f"⚠️ After payment, send screenshot as proof"
        
        return text
    
    @staticmethod
    def get_proof_keyboard(deposit_id: str) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="✅ Proof Sent", callback_data=f"proof_sent_{deposit_id}")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="wallet")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def calculate_points_from_stars(stars: int) -> int:
        """Calculate points from Telegram Stars"""
        return int(stars * config.STARS_TO_POINTS)
    
    @staticmethod
    def calculate_points_from_usd(usd: float) -> int:
        """Calculate points from USD"""
        return int(usd * config.CRYPTO_TO_POINTS)
    
    @staticmethod
    def calculate_usd_from_points(points: int) -> float:
        """Calculate USD from points"""
        return points * config.POINTS_TO_USD
