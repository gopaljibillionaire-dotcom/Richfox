from motor.motor_asyncio import AsyncIOMotorClient
from config import config
from datetime import datetime
from typing import Optional, Dict, Any

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(config.MONGO_URI)
        self.db = self.client.games_bot
        self.users = self.db.users
        self.games = self.db.games
        self.transactions = self.db.transactions
        self.withdrawals = self.db.withdrawals
        
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        user = await self.users.find_one({"user_id": user_id})
        if not user:
            user = {
                "user_id": user_id,
                "points": 0,
                "games_played": 0,
                "games_won": 0,
                "created_at": datetime.utcnow()
            }
            await self.users.insert_one(user)
        return user
    
    async def update_points(self, user_id: int, points: int) -> bool:
        result = await self.users.update_one(
            {"user_id": user_id},
            {"$inc": {"points": points}}
        )
        return result.modified_count > 0
    
    async def get_points(self, user_id: int) -> int:
        user = await self.get_user(user_id)
        return user.get("points", 0)
    
    async def deduct_points(self, user_id: int, points: int) -> bool:
        user = await self.get_user(user_id)
        if user.get("points", 0) >= points:
            await self.update_points(user_id, -points)
            return True
        return False
    
    async def create_game(self, game_data: Dict[str, Any]) -> str:
        result = await self.games.insert_one(game_data)
        return str(result.inserted_id)
    
    async def get_game(self, game_id: str):
        from bson import ObjectId
        return await self.games.find_one({"_id": ObjectId(game_id)})
    
    async def update_game(self, game_id: str, update_data: Dict[str, Any]):
        from bson import ObjectId
        await self.games.update_one(
            {"_id": ObjectId(game_id)},
            {"$set": update_data}
        )
    
    async def delete_game(self, game_id: str):
        from bson import ObjectId
        await self.games.delete_one({"_id": ObjectId(game_id)})
    
    async def add_transaction(self, transaction_data: Dict[str, Any]):
        transaction_data["created_at"] = datetime.utcnow()
        await self.transactions.insert_one(transaction_data)
    
    async def create_withdrawal(self, withdrawal_data: Dict[str, Any]) -> str:
        withdrawal_data["status"] = "pending"
        withdrawal_data["created_at"] = datetime.utcnow()
        result = await self.withdrawals.insert_one(withdrawal_data)
        return str(result.inserted_id)
    
    async def get_withdrawal(self, withdrawal_id: str):
        from bson import ObjectId
        return await self.withdrawals.find_one({"_id": ObjectId(withdrawal_id)})
    
    async def update_withdrawal_status(self, withdrawal_id: str, status: str):
        from bson import ObjectId
        await self.withdrawals.update_one(
            {"_id": ObjectId(withdrawal_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
    
    async def update_stats(self, user_id: int, won: bool = False):
        update_data = {"$inc": {"games_played": 1}}
        if won:
            update_data["$inc"]["games_won"] = 1
        await self.users.update_one({"user_id": user_id}, update_data)

db = Database()
