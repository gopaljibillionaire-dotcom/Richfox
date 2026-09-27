import random
from typing import List, Optional, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

class TicTacToe:
    def __init__(self, player1_id: int, player2_id: int, bet: int):
        self.board = [" " for _ in range(9)]
        self.players = {player1_id: "❌", player2_id: "⭕"}
        self.player_ids = [player1_id, player2_id]
        random.shuffle(self.player_ids)
        self.current_player_idx = 0
        self.bet = bet
        self.winner = None
        
    def get_current_player(self) -> int:
        return self.player_ids[self.current_player_idx]
    
    def get_symbol(self, player_id: int) -> str:
        return self.players.get(player_id, " ")
    
    def make_move(self, player_id: int, position: int) -> bool:
        if self.board[position] == " " and player_id == self.get_current_player():
            self.board[position] = self.get_symbol(player_id)
            if not self.check_winner():
                self.current_player_idx = 1 - self.current_player_idx
            return True
        return False
    
    def check_winner(self) -> Optional[int]:
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]
        
        for combo in winning_combinations:
            if (self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]] != " "):
                for player_id, symbol in self.players.items():
                    if self.board[combo[0]] == symbol:
                        self.winner = player_id
                        return player_id
        
        if " " not in self.board:
            self.winner = 0  # Draw
            return 0
        
        return None
    
    def get_keyboard(self, game_id: str) -> InlineKeyboardMarkup:
        keyboard = []
        for i in range(0, 9, 3):
            row = []
            for j in range(3):
                pos = i + j
                text = self.board[pos] if self.board[pos] != " " else "⬜"
                row.append(InlineKeyboardButton(
                    text=text,
                    callback_data=f"ttt_{game_id}_{pos}"
                ))
            keyboard.append(row)
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def get_status_text(self) -> str:
        current = self.get_current_player()
        symbol = self.get_symbol(current)
        
        text = f"🎮 **Tic-Tac-Toe**\n"
        text += f"💰 Bet: {self.bet} points\n\n"
        
        for player_id, sym in self.players.items():
            text += f"{sym} Player: {player_id}\n"
        
        text += f"\n🎯 Current turn: {symbol} (Player {current})"
        return text


class DiceDuel:
    def __init__(self, player1_id: int, player2_id: int, bet: int):
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.bet = bet
        self.player1_roll = None
        self.player2_roll = None
        self.winner = None
        
    def roll(self, player_id: int) -> int:
        roll = random.randint(1, 6)
        if player_id == self.player1_id:
            self.player1_roll = roll
        else:
            self.player2_roll = roll
        
        if self.player1_roll and self.player2_roll:
            if self.player1_roll > self.player2_roll:
                self.winner = self.player1_id
            elif self.player2_roll > self.player1_roll:
                self.winner = self.player2_id
            else:
                self.winner = 0  # Draw
        
        return roll
    
    def is_complete(self) -> bool:
        return self.player1_roll is not None and self.player2_roll is not None


class Limbo:
    def __init__(self, player_id: int, bet: int, target: float):
        self.player_id = player_id
        self.bet = bet
        self.target = target
        self.result = None
        self.won = False
        
    def play(self) -> Tuple[float, bool]:
        # Generate random multiplier between 1.00 and 100.00
        self.result = round(random.uniform(1.00, 100.00), 2)
        self.won = self.result >= self.target
        return self.result, self.won
    
    def get_winnings(self) -> int:
        if self.won:
            return int(self.bet * self.target)
        return 0


class SlotMachine:
    SYMBOLS = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎", "7️⃣"]
    
    def __init__(self, player_id: int, bet: int):
        self.player_id = player_id
        self.bet = bet
        self.reels = []
        self.won = False
        self.winnings = 0
        
    def spin(self) -> Tuple[List[str], int]:
        self.reels = [random.choice(self.SYMBOLS) for _ in range(3)]
        
        # Calculate winnings
        if self.reels[0] == self.reels[1] == self.reels[2]:
            if self.reels[0] == "💎":
                self.winnings = self.bet * 10
            elif self.reels[0] == "7️⃣":
                self.winnings = self.bet * 7
            elif self.reels[0] == "⭐":
                self.winnings = self.bet * 5
            else:
                self.winnings = self.bet * 3
            self.won = True
        elif self.reels[0] == self.reels[1] or self.reels[1] == self.reels[2]:
            self.winnings = self.bet * 2
            self.won = True
        
        return self.reels, self.winnings


class QuizBattle:
    QUESTIONS = [
        {
            "question": "What is the capital of France?",
            "options": ["London", "Berlin", "Paris", "Madrid"],
            "answer": 2
        },
        {
            "question": "What is 2 + 2?",
            "options": ["3", "4", "5", "6"],
            "answer": 1
        },
        {
            "question": "Which planet is known as the Red Planet?",
            "options": ["Venus", "Mars", "Jupiter", "Saturn"],
            "answer": 1
        },
        {
            "question": "Who painted the Mona Lisa?",
            "options": ["Van Gogh", "Picasso", "Da Vinci", "Monet"],
            "answer": 2
        },
        {
            "question": "What is the largest ocean?",
            "options": ["Atlantic", "Indian", "Arctic", "Pacific"],
            "answer": 3
        }
    ]
    
    def __init__(self, player1_id: int, player2_id: int, bet: int):
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.bet = bet
        self.question = random.choice(self.QUESTIONS)
        self.player1_answer = None
        self.player2_answer = None
        self.winner = None
        
    def answer(self, player_id: int, answer_idx: int):
        if player_id == self.player1_id:
            self.player1_answer = answer_idx
        else:
            self.player2_answer = answer_idx
        
        if self.player1_answer is not None and self.player2_answer is not None:
            correct = self.question["answer"]
            p1_correct = self.player1_answer == correct
            p2_correct = self.player2_answer == correct
            
            if p1_correct and not p2_correct:
                self.winner = self.player1_id
            elif p2_correct and not p1_correct:
                self.winner = self.player2_id
            else:
                self.winner = 0  # Draw
    
    def get_keyboard(self, game_id: str) -> InlineKeyboardMarkup:
        keyboard = []
        for idx, option in enumerate(self.question["options"]):
            keyboard.append([InlineKeyboardButton(
                text=option,
                callback_data=f"quiz_{game_id}_{idx}"
            )])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def is_complete(self) -> bool:
        return self.player1_answer is not None and self.player2_answer is not None
