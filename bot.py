import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from config import config
from database import db
from games import TicTacToe, DiceDuel, Limbo, SlotMachine, QuizBattle
from payments import PaymentHandler
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# Active games storage
active_games = {}
pending_games = {}

# FSM States
class DepositStates(StatesGroup):
    waiting_amount = State()
    waiting_proof = State()

class WithdrawStates(StatesGroup):
    waiting_amount = State()
    waiting_address = State()

class GameStates(StatesGroup):
    waiting_bet = State()
    waiting_join = State()
    waiting_target = State()

# Helper Functions
def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="💰 Wallet", callback_data="wallet"),
            InlineKeyboardButton(text="📊 Stats", callback_data="stats")
        ],
        [
            InlineKeyboardButton(text="🎮 How to Play", callback_data="help")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_wallet_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="💵 Deposit", callback_data="deposit", style="success")],
        [InlineKeyboardButton(text="💸 Withdraw", callback_data="withdraw", style="danger")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="start")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_games_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="⭕ Tic-Tac-Toe", callback_data="game_ttt"),
            InlineKeyboardButton(text="🎲 Dice Duel", callback_data="game_dice")
        ],
        [
            InlineKeyboardButton(text="🎰 Slot Machine", callback_data="game_slot"),
            InlineKeyboardButton(text="📈 Limbo", callback_data="game_limbo")
        ],
        [
            InlineKeyboardButton(text="❓ Quiz Battle", callback_data="game_quiz")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Command Handlers
@router.message(CommandStart())
async def cmd_start(message: Message):
    if message.chat.type == "private":
        user = await db.get_user(message.from_user.id)
        text = f"👋 Welcome to **Games Bot**!\n\n"
        text += f"💰 Your Balance: **{user['points']}** points\n\n"
        text += f"Play games in group chats and manage your wallet here!"
        
        await message.answer(text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    else:
        await message.answer("👋 Hello! Use /ttt, /dice, /slot, /limbo, or /quiz to start a game!")

@router.message(Command("ttt"))
async def cmd_ttt(message: Message, state: FSMContext):
    if message.chat.type == "private":
        await message.answer("❌ This game can only be played in groups!")
        return
    
    await message.answer("💰 How many points do you want to bet?")
    await state.set_state(GameStates.waiting_bet)
    await state.update_data(game_type="ttt", player1=message.from_user.id, chat_id=message.chat.id)

@router.message(Command("dice"))
async def cmd_dice(message: Message, state: FSMContext):
    if message.chat.type == "private":
        await message.answer("❌ This game can only be played in groups!")
        return
    
    await message.answer("💰 How many points do you want to bet?")
    await state.set_state(GameStates.waiting_bet)
    await state.update_data(game_type="dice", player1=message.from_user.id, chat_id=message.chat.id)

@router.message(Command("quiz"))
async def cmd_quiz(message: Message, state: FSMContext):
    if message.chat.type == "private":
        await message.answer("❌ This game can only be played in groups!")
        return
    
    await message.answer("💰 How many points do you want to bet?")
    await state.set_state(GameStates.waiting_bet)
    await state.update_data(game_type="quiz", player1=message.from_user.id, chat_id=message.chat.id)

@router.message(Command("slot"))
async def cmd_slot(message: Message, state: FSMContext):
    if message.chat.type == "private":
        await message.answer("❌ This game can only be played in groups!")
        return
    
    await message.answer("💰 How many points do you want to bet?")
    await state.set_state(GameStates.waiting_bet)
    await state.update_data(game_type="slot", player1=message.from_user.id, chat_id=message.chat.id, solo=True)

@router.message(Command("limbo"))
async def cmd_limbo(message: Message, state: FSMContext):
    if message.chat.type == "private":
        await message.answer("❌ This game can only be played in groups!")
        return
    
    await message.answer("💰 How many points do you want to bet?")
    await state.set_state(GameStates.waiting_bet)
    await state.update_data(game_type="limbo", player1=message.from_user.id, chat_id=message.chat.id, solo=True)

# Bet Handler
@router.message(GameStates.waiting_bet)
async def process_bet(message: Message, state: FSMContext):
    try:
        bet = int(message.text)
        if bet < 10:
            await message.answer("❌ Minimum bet is 10 points!")
            return
        
        user_points = await db.get_points(message.from_user.id)
        if user_points < bet:
            await message.answer(f"❌ Insufficient balance! You have {user_points} points.")
            return
        
        data = await state.get_data()
        game_type = data['game_type']
        
        # Solo games
        if data.get('solo'):
            if game_type == "slot":
                await play_slot_machine(message, bet, state)
            elif game_type == "limbo":
                await message.answer("🎯 Enter target multiplier (1.00 - 100.00):")
                await state.update_data(bet=bet)
                await state.set_state(GameStates.waiting_target)
            return
        
        # Multiplayer games
        await db.deduct_points(message.from_user.id, bet)
        
        game_id = f"{message.chat.id}_{message.from_user.id}_{datetime.now().timestamp()}"
        pending_games[game_id] = {
            "type": game_type,
            "player1": message.from_user.id,
            "bet": bet,
            "chat_id": message.chat.id
        }
        
        keyboard = [[InlineKeyboardButton(
            text="🎮 Join Game",
            callback_data=f"join_{game_id}",
            style="success"
        )]]
        
        await message.answer(
            f"🎮 **{message.from_user.first_name}** started a **{game_type.upper()}** game!\n"
            f"💰 Bet: {bet} points\n\n"
            f"👥 Waiting for opponent...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Please enter a valid number!")

# Limbo target handler
@router.message(GameStates.waiting_target)
async def process_limbo_target(message: Message, state: FSMContext):
    try:
        target = float(message.text)
        if target < 1.0 or target > 100.0:
            await message.answer("❌ Target must be between 1.00 and 100.00!")
            return
        
        data = await state.get_data()
        bet = data['bet']
        
        user_points = await db.get_points(message.from_user.id)
        if user_points < bet:
            await message.answer(f"❌ Insufficient balance! You have {user_points} points.")
            await state.clear()
            return
        
        await db.deduct_points(message.from_user.id, bet)
        
        game = Limbo(message.from_user.id, bet, target)
        result, won = game.play()
        
        if won:
            winnings = game.get_winnings()
            await db.update_points(message.from_user.id, winnings)
            await db.update_stats(message.from_user.id, won=True)
            
            text = f"🎉 **WIN!**\n\n"
            text += f"🎯 Target: {target:.2f}x\n"
            text += f"🎲 Result: {result:.2f}x\n"
            text += f"💰 Won: {winnings} points!"
        else:
            await db.update_stats(message.from_user.id, won=False)
            text = f"😢 **LOSS!**\n\n"
            text += f"🎯 Target: {target:.2f}x\n"
            text += f"🎲 Result: {result:.2f}x\n"
            text += f"💸 Lost: {bet} points"
        
        await message.answer(text, parse_mode="Markdown")
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Please enter a valid number!")

# Slot machine handler
async def play_slot_machine(message: Message, bet: int, state: FSMContext):
    user_points = await db.get_points(message.from_user.id)
    if user_points < bet:
        await message.answer(f"❌ Insufficient balance! You have {user_points} points.")
        await state.clear()
        return
    
    await db.deduct_points(message.from_user.id, bet)
    
    game = SlotMachine(message.from_user.id, bet)
    reels, winnings = game.spin()
    
    result_text = " | ".join(reels)
    
    if game.won:
        await db.update_points(message.from_user.id, winnings)
        await db.update_stats(message.from_user.id, won=True)
        text = f"🎰 **SLOT MACHINE**\n\n"
        text += f"{result_text}\n\n"
        text += f"🎉 **WIN!**\n"
        text += f"💰 Won: {winnings} points!"
    else:
        await db.update_stats(message.from_user.id, won=False)
        text = f"🎰 **SLOT MACHINE**\n\n"
        text += f"{result_text}\n\n"
        text += f"😢 Better luck next time!\n"
        text += f"💸 Lost: {bet} points"
    
    await message.answer(text, parse_mode="Markdown")
    await state.clear()

# Join game callback
@router.callback_query(F.data.startswith("join_"))
async def join_game(callback: CallbackQuery):
    game_id = callback.data.split("_", 1)[1]
    
    if game_id not in pending_games:
        await callback.answer("❌ Game no longer available!", show_alert=True)
        return
    
    game_data = pending_games[game_id]
    
    if callback.from_user.id == game_data['player1']:
        await callback.answer("❌ You can't join your own game!", show_alert=True)
        return
    
    bet = game_data['bet']
    user_points = await db.get_points(callback.from_user.id)
    
    if user_points < bet:
        await callback.answer(f"❌ You need {bet} points to join!", show_alert=True)
        return
    
    await db.deduct_points(callback.from_user.id, bet)
    
    game_type = game_data['type']
    player1 = game_data['player1']
    player2 = callback.from_user.id
    
    if game_type == "ttt":
        game = TicTacToe(player1, player2, bet)
        active_games[game_id] = game
        
        await callback.message.edit_text(
            game.get_status_text(),
            reply_markup=game.get_keyboard(game_id),
            parse_mode="Markdown"
        )
    
    elif game_type == "dice":
        game = DiceDuel(player1, player2, bet)
        active_games[game_id] = game
        
        keyboard = [
            [InlineKeyboardButton(text="🎲 Roll Dice", callback_data=f"roll_{game_id}", style="primary")]
        ]
        
        await callback.message.edit_text(
            f"🎲 **Dice Duel**\n"
            f"💰 Bet: {bet} points\n\n"
            f"Player 1: {player1}\n"
            f"Player 2: {player2}\n\n"
            f"Click to roll your dice!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
    
    elif game_type == "quiz":
        game = QuizBattle(player1, player2, bet)
        active_games[game_id] = game
        
        await callback.message.edit_text(
            f"❓ **Quiz Battle**\n"
            f"💰 Bet: {bet} points\n\n"
            f"Question: {game.question['question']}\n\n"
            f"Choose your answer:",
            reply_markup=game.get_keyboard(game_id),
            parse_mode="Markdown"
        )
    
    del pending_games[game_id]
    await callback.answer("✅ Joined game!")

# Tic-Tac-Toe move
@router.callback_query(F.data.startswith("ttt_"))
async def ttt_move(callback: CallbackQuery):
    parts = callback.data.split("_")
    game_id = parts[1]
    position = int(parts[2])
    
    if game_id not in active_games:
        await callback.answer("❌ Game not found!", show_alert=True)
        return
    
    game = active_games[game_id]
    
    if callback.from_user.id not in game.player_ids:
        await callback.answer("❌ You're not in this game!", show_alert=True)
        return
    
    if not game.make_move(callback.from_user.id, position):
        await callback.answer("❌ Invalid move!", show_alert=True)
        return
    
    winner = game.check_winner()
    
    if winner is not None:
        if winner == 0:
            # Draw
            await db.update_points(game.player_ids[0], game.bet)
            await db.update_points(game.player_ids[1], game.bet)
            result_text = "🤝 **It's a draw!**\nBets returned."
        else:
            # Winner
            loser = game.player_ids[0] if winner == game.player_ids[1] else game.player_ids[1]
            await db.update_points(winner, game.bet * 2)
            await db.update_stats(winner, won=True)
            await db.update_stats(loser, won=False)
            
            result_text = f"🎉 **Player {winner} wins!**\n💰 Won: {game.bet * 2} points!"
        
        await callback.message.edit_text(
            game.get_status_text() + f"\n\n{result_text}",
            parse_mode="Markdown"
        )
        del active_games[game_id]
    else:
        await callback.message.edit_text(
            game.get_status_text(),
            reply_markup=game.get_keyboard(game_id),
            parse_mode="Markdown"
        )
    
    await callback.answer()

# Dice roll
@router.callback_query(F.data.startswith("roll_"))
async def dice_roll(callback: CallbackQuery):
    game_id = callback.data.split("_", 1)[1]
    
    if game_id not in active_games:
        await callback.answer("❌ Game not found!", show_alert=True)
        return
    
    game = active_games[game_id]
    
    if callback.from_user.id not in [game.player1_id, game.player2_id]:
        await callback.answer("❌ You're not in this game!", show_alert=True)
        return
    
    if callback.from_user.id == game.player1_id and game.player1_roll:
        await callback.answer("❌ You already rolled!", show_alert=True)
        return
    
    if callback.from_user.id == game.player2_id and game.player2_roll:
        await callback.answer("❌ You already rolled!", show_alert=True)
        return
    
    roll = game.roll(callback.from_user.id)
    
    dice_msg = await callback.message.answer_dice("🎲")
    await asyncio.sleep(3)
    
    if game.is_complete():
        if game.winner == 0:
            await db.update_points(game.player1_id, game.bet)
            await db.update_points(game.player2_id, game.bet)
            result_text = f"🤝 **It's a draw!** ({game.player1_roll} - {game.player2_roll})\nBets returned."
        else:
            loser = game.player1_id if game.winner == game.player2_id else game.player2_id
            await db.update_points(game.winner, game.bet * 2)
            await db.update_stats(game.winner, won=True)
            await db.update_stats(loser, won=False)
            
            result_text = f"🎉 **Player {game.winner} wins!**\n"
            result_text += f"🎲 {game.player1_roll} vs {game.player2_roll}\n"
            result_text += f"💰 Won: {game.bet * 2} points!"
        
        await callback.message.edit_text(result_text, parse_mode="Markdown")
        del active_games[game_id]
    else:
        await callback.message.edit_text(
            f"🎲 **Dice Duel**\n"
            f"💰 Bet: {game.bet} points\n\n"
            f"Player 1: {'🎲' + str(game.player1_roll) if game.player1_roll else '⏳ Waiting...'}\n"
            f"Player 2: {'🎲' + str(game.player2_roll) if game.player2_roll else '⏳ Waiting...'}\n\n"
            f"Waiting for other player...",
            parse_mode="Markdown"
        )
    
    await callback.answer(f"You rolled: {roll}")

# Quiz answer
@router.callback_query(F.data.startswith("quiz_"))
async def quiz_answer(callback: CallbackQuery):
    parts = callback.data.split("_")
    game_id = parts[1]
    answer_idx = int(parts[2])
    
    if game_id not in active_games:
        await callback.answer("❌ Game not found!", show_alert=True)
        return
    
    game = active_games[game_id]
    
    if callback.from_user.id not in [game.player1_id, game.player2_id]:
        await callback.answer("❌ You're not in this game!", show_alert=True)
        return
    
    game.answer(callback.from_user.id, answer_idx)
    
    if game.is_complete():
        correct_answer = game.question["options"][game.question["answer"]]
        
        if game.winner == 0:
            await db.update_points(game.player1_id, game.bet)
            await db.update_points(game.player2_id, game.bet)
            result_text = f"🤝 **It's a draw!**\n✅ Correct: {correct_answer}\nBets returned."
        else:
            loser = game.player1_id if game.winner == game.player2_id else game.player2_id
            await db.update_points(game.winner, game.bet * 2)
            await db.update_stats(game.winner, won=True)
            await db.update_stats(loser, won=False)
            
            result_text = f"🎉 **Player {game.winner} wins!**\n"
            result_text += f"✅ Correct: {correct_answer}\n"
            result_text += f"💰 Won: {game.bet * 2} points!"
        
        await callback.message.edit_text(
            f"❓ **Quiz Battle Results**\n\n"
            f"Question: {game.question['question']}\n\n"
            f"{result_text}",
            parse_mode="Markdown"
        )
        del active_games[game_id]
    else:
        await callback.answer("✅ Answer submitted! Waiting for opponent...")
    
    await callback.answer()

# Wallet handlers
@router.callback_query(F.data == "wallet")
async def show_wallet(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    
    text = f"💰 **Your Wallet**\n\n"
    text += f"Balance: **{user['points']}** points\n"
    text += f"≈ ${user['points'] * config.POINTS_TO_USD:.2f} USD\n\n"
    text += f"🎮 Games Played: {user['games_played']}\n"
    text += f"🏆 Games Won: {user['games_won']}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_wallet_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Deposit handlers
@router.callback_query(F.data == "deposit")
async def start_deposit(callback: CallbackQuery):
    text = "💵 **Deposit Points**\n\n"
    text += "Choose payment method:"
    
    await callback.message.edit_text(
        text,
        reply_markup=PaymentHandler.get_deposit_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "deposit_stars")
async def deposit_stars(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "⭐ **Deposit with Telegram Stars**\n\n"
        "Enter amount in USD (1$ = 100 points):\n"
        "Example: 10",
        parse_mode="Markdown"
    )
    await state.set_state(DepositStates.waiting_amount)
    await state.update_data(method="stars")
    await callback.answer()

@router.callback_query(F.data == "deposit_crypto_auto")
async def deposit_crypto_auto(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💳 **Crypto Deposit (Automatic)**\n\n"
        "Enter amount in USD (1$ = 100 points):\n"
        "Example: 10",
        parse_mode="Markdown"
    )
    await state.set_state(DepositStates.waiting_amount)
    await state.update_data(method="crypto_auto")
    await callback.answer()

@router.callback_query(F.data == "deposit_crypto_manual")
async def deposit_crypto_manual(callback: CallbackQuery):
    await callback.message.edit_text(
        "💰 **Manual Crypto Deposit**\n\n"
        "Select cryptocurrency:",
        reply_markup=PaymentHandler.get_crypto_selection_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("crypto_"))
async def select_crypto(callback: CallbackQuery, state: FSMContext):
    crypto_type = callback.data
    
    await callback.message.edit_text(
        f"Enter amount in USD (1$ = 100 points):\n"
        f"Example: 10",
        parse_mode="Markdown"
    )
    await state.set_state(DepositStates.waiting_amount)
    await state.update_data(method="crypto_manual", crypto_type=crypto_type)
    await callback.answer()

# Amount handler for deposits
@router.message(DepositStates.waiting_amount)
async def process_deposit_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount < 1:
            await message.answer("❌ Minimum deposit is $1!")
            return
        
        data = await state.get_data()
        method = data['method']
        
        if method == "stars":
            # Telegram Stars payment
            stars = int(amount * 100)  # 1 USD = 100 stars
            points = PaymentHandler.calculate_points_from_stars(stars)
            
            # Note: Actual Stars API implementation would go here
            await message.answer(
                f"⭐ **Stars Payment**\n\n"
                f"Amount: {stars} stars\n"
                f"Points: {points}\n\n"
                f"⚠️ Stars payment integration requires bot verification.\n"
                f"Contact @BotSupport to enable payments.",
                parse_mode="Markdown"
            )
            await state.clear()
            
        elif method == "crypto_auto":
            # OxaPay automatic payment
            payment = await PaymentHandler.create_oxapay_payment(amount)
            
            if payment and payment.get("result") == 100:
                pay_link = payment.get("payLink")
                track_id = payment.get("trackId")
                
                keyboard = [[
                    InlineKeyboardButton(text="💳 Pay Now", url=pay_link),
                    InlineKeyboardButton(text="✅ Check Payment", callback_data=f"check_payment_{track_id}")
                ]]
                
                points = PaymentHandler.calculate_points_from_usd(amount)
                
                await message.answer(
                    f"💳 **Crypto Payment**\n\n"
                    f"Amount: ${amount:.2f}\n"
                    f"Points: {points}\n\n"
                    f"Click button to complete payment:",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                    parse_mode="Markdown"
                )
                await state.clear()
            else:
                await message.answer("❌ Failed to create payment. Try again later.")
                await state.clear()
        
        elif method == "crypto_manual":
            crypto_type = data['crypto_type']
            points = PaymentHandler.calculate_points_from_usd(amount)
            
            deposit_id = await db.create_game({
                "type": "deposit",
                "user_id": message.from_user.id,
                "amount": amount,
                "points": points,
                "crypto_type": crypto_type,
                
