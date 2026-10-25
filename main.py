import os
import random
import asyncio
import io
import json
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from gtts import gTTS
import uvicorn

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://habeshabingo.tail1a2d47.ts.net/')
PORT = int(os.getenv('PORT', 8000))
BOT_NAME = os.getenv('BOT_NAME', 'Habesha BINGO')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'BingoHabeshaGameBot')

# ===== GAME STATE =====
active_games = {}
game_players = {}

class BingoGame:
    def __init__(self, game_id, admin_id):
        self.game_id = game_id
        self.admin_id = admin_id
        self.players = {}
        self.called_numbers = []
        self.status = "waiting"
        self.created_at = datetime.now()
        self.current_number = None
        self.prize_pool = 0
        self.bet_amount = 10
        
    def generate_card(self):
        """Generate a random Bingo card"""
        card = {}
        card['B'] = sorted(random.sample(range(1, 16), 5))
        card['I'] = sorted(random.sample(range(16, 31), 5))
        card['N'] = sorted(random.sample(range(31, 46), 5))
        card['G'] = sorted(random.sample(range(46, 61), 5))
        card['O'] = sorted(random.sample(range(61, 76), 5))
        return card
    
    def add_player(self, user_id, username):
        if user_id not in self.players:
            self.players[user_id] = {
                'card': self.generate_card(),
                'marked': set(),
                'username': username,
                'joined_at': datetime.now()
            }
            self.prize_pool += self.bet_amount
            return True
        return False
    
    def draw_number(self):
        available = [n for n in range(1, 76) if n not in self.called_numbers]
        if not available:
            return None
        number = random.choice(available)
        self.called_numbers.append(number)
        self.current_number = number
        return number
    
    def mark_number(self, user_id, number):
        if user_id not in self.players:
            return False
        if number not in self.called_numbers:
            return False
        self.players[user_id]['marked'].add(number)
        return True
    
    def check_bingo(self, user_id):
        if user_id not in self.players:
            return False
        
        player = self.players[user_id]
        card = player['card']
        marked = player['marked']
        
        # Check rows
        for row in range(5):
            if all(card[col][row] in marked for col in ['B','I','N','G','O']):
                return True
        
        # Check columns
        for col in ['B','I','N','G','O']:
            if all(card[col][row] in marked for row in range(5)):
                return True
        
        # Check diagonals
        if all(card[['B','I','N','G','O'][i]][i] in marked for i in range(5)):
            return True
        if all(card[['B','I','N','G','O'][i]][4-i] in marked for i in range(5)):
            return True
        
        return False
    
    def get_card_for_user(self, user_id):
        if user_id not in self.players:
            return None
        return self.players[user_id]['card']
    
    def get_marked_for_user(self, user_id):
        if user_id not in self.players:
            return []
        return list(self.players[user_id]['marked'])
    
    def to_dict(self):
        return {
            'game_id': self.game_id,
            'status': self.status,
            'called_numbers': self.called_numbers,
            'current_number': self.current_number,
            'players_count': len(self.players),
            'prize_pool': self.prize_pool,
            'bet_amount': self.bet_amount,
            'created_at': self.created_at.isoformat()
        }

# ===== TELEGRAM BOT HANDLERS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    game_id = f"HAB_{int(datetime.now().timestamp())}"
    
    if game_id not in active_games:
        active_games[game_id] = BingoGame(game_id, user.id)
    
    game = active_games[game_id]
    game.add_player(user.id, user.username or user.first_name)
    
    context.user_data['game_id'] = game_id
    
    keyboard = [[
        InlineKeyboardButton(
            "🎯 የቢንጎ ካርድ ክፈት / Open Card",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}?game_id={game_id}")
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🇪🇹 **ሐበሻ ቢንጎ / Habesha BINGO**\n"
        f"🤖 @{BOT_USERNAME}\n\n"
        f"👋 እንኳን ደህና መጣህ, {user.first_name}!\n\n"
        f"📊 የጨዋታ መለያ / Game ID: `{game_id}`\n"
        f"💰 ውርርድ / Bet: {game.bet_amount} ETB\n"
        f"🏆 ሽልማት / Prize Pool: {game.prize_pool} ETB\n"
        f"👥 ተጫዋቾች / Players: {len(game.players)}\n\n"
        f"👇 ካርዱን ለመክፈት ቁልፉን ተጫን\n"
        f"Click the button below to open your card!\n\n"
        f"📌 **Commands:**\n"
        f"• /draw - ቁጥር ጥራ (Admin only)\n"
        f"• /status - ሁኔታ ተመልከት\n"
        f"• /help - እርዳታ",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to draw a number"""
    user_id = update.effective_user.id
    game_id = context.user_data.get('game_id')
    
    if not game_id or game_id not in active_games:
        await update.message.reply_text("❌ ምንም ንቁ ጨዋታ የለም! / No active game!")
        return
    
    game = active_games[game_id]
    
    if game.admin_id != user_id:
        await update.message.reply_text("❌ ይህን ማድረግ የሚችለው የጨዋታው አስተዳዳሪ ብቻ ነው!")
        return
    
    if game.status == "finished":
        await update.message.reply_text("❌ ይህ ጨዋታ አልቋል! / This game is finished!")
        return
    
    number = game.draw_number()
    if not number:
        game.status = "finished"
        await update.message.reply_text("🎉 ሁሉም ቁጥሮች ተጠርተዋል! ጨዋታ አልቋል!")
        return
    
    await send_voice_call(update, context, number)
    
    await update.message.reply_text(
        f"🎲 ቁጥር / Number: **{number}**\n"
        f"📊 የተጠሩ / Called: {len(game.called_numbers)}/75",
        parse_mode='Markdown'
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check game status"""
    game_id = context.user_data.get('game_id')
    
    if not game_id or game_id not in active_games:
        await update.message.reply_text("❌ ምንም ንቁ ጨዋታ የለም!")
        return
    
    game = active_games[game_id]
    await update.message.reply_text(
        f"📊 **የጨዋታ ሁኔታ / Game Status**\n\n"
        f"🆔 መለያ / ID: `{game.game_id}`\n"
        f"👥 ተጫዋቾች / Players: {len(game.players)}\n"
        f"🎲 የተጠሩ / Called: {len(game.called_numbers)}/75\n"
        f"💰 ሽልማት / Prize Pool: {game.prize_pool} ETB\n"
        f"📌 ሁኔታ / Status: {game.status.upper()}",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show commands and the official Habesha Bingo group."""
    await update.message.reply_text(
        f"🇪🇹 **ሐበሻ ቢንጎ / Habesha BINGO**\n"
        f"🤖 @{BOT_USERNAME}\n\n"
        f"📌 **Commands:**\n"
        f"• `/start` - Open Habesha Bingo\n"
        f"• `/draw` - Draw a number (admin only)\n"
        f"• `/status` - Check game status\n"
        f"• `/help` - Show this help\n"
        f"• `/contact` - Contact our agents\n\n"
        f"👥 Official group: https://t.me/HabeshaBingoOfficial\n"
        f"📞 Agent: @HabeshaBingo251",
        parse_mode='Markdown'
    )

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the official Habesha Bingo agent contact."""
    await update.message.reply_text(
        "🇪🇹 **Habesha Bingo — Contact Agents**\n\n"
        "📞 Agent: @HabeshaBingo251\n"
        "👥 Official group: https://t.me/HabeshaBingoOfficial",
        parse_mode='Markdown'
    )

async def send_voice_call(update: Update, context: ContextTypes.DEFAULT_TYPE, number):
    """Send voice message for the called number"""
    try:
        amharic_numbers = {
            1: 'አንድ', 2: 'ሁለት', 3: 'ሶስት', 4: 'አራት', 5: 'አምስት',
            6: 'ስድስት', 7: 'ሰባት', 8: 'ስምንት', 9: 'ዘጠኝ', 10: 'አስር',
            11: 'አስራ አንድ', 12: 'አስራ ሁለት', 13: 'አስራ ሶስት', 14: 'አስራ አራት', 15: 'አስራ አምስት',
            16: 'አስራ ስድስት', 17: 'አስራ ሰባት', 18: 'አስራ ስምንት', 19: 'አስራ ዘጠኝ', 20: 'ሃያ'
        }
        
        amharic_num = amharic_numbers.get(number, str(number))
        
        tts = gTTS(text=f"ቁጥር {amharic_num} . Number {number}", lang='am', slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        await context.bot.send_voice(
            chat_id=update.effective_chat.id,
            voice=audio_buffer,
            caption=f"🔊 ቁጥር / Number: {number}"
        )
    except Exception as e:
        print(f"Voice error: {e}")
        await update.message.reply_text(f"🔊 ቁጥር / Number {number} ተጠርቷል / called!")

# ===== FASTAPI WEBAPP =====

app = FastAPI(title="Habesha BINGO API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections = {}

@app.websocket("/ws/{game_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, user_id: str):
    await websocket.accept()
    
    if game_id not in active_connections:
        active_connections[game_id] = {}
    active_connections[game_id][user_id] = websocket
    
    try:
        game = active_games.get(game_id)
        if game:
            await websocket.send_json({
                'type': 'game_state',
                'data': game.to_dict(),
                'card': game.get_card_for_user(int(user_id)),
                'marked': game.get_marked_for_user(int(user_id))
            })
        
        while True:
            data = await websocket.receive_json()
            
            if data['type'] == 'mark_number':
                game = active_games.get(game_id)
                if game:
                    number = data['number']
                    success = game.mark_number(int(user_id), number)
                    await websocket.send_json({
                        'type': 'mark_ack',
                        'success': success,
                        'number': number
                    })
                    await broadcast_game_update(game_id)
            
            elif data['type'] == 'check_bingo':
                game = active_games.get(game_id)
                if game:
                    is_bingo = game.check_bingo(int(user_id))
                    await websocket.send_json({
                        'type': 'bingo_result',
                        'is_bingo': is_bingo,
                        'user_id': user_id
                    })
                    
                    if is_bingo:
                        game.status = "finished"
                        await broadcast_game_update(game_id)
            
            elif data['type'] == 'request_update':
                game = active_games.get(game_id)
                if game:
                    await websocket.send_json({
                        'type': 'game_state',
                        'data': game.to_dict(),
                        'card': game.get_card_for_user(int(user_id)),
                        'marked': game.get_marked_for_user(int(user_id))
                    })
    
    except WebSocketDisconnect:
        if game_id in active_connections:
            active_connections[game_id].pop(user_id, None)
    except Exception as e:
        print(f"WebSocket error: {e}")

async def broadcast_game_update(game_id: str):
    game = active_games.get(game_id)
    if not game:
        return
    
    if game_id not in active_connections:
        return
    
    for user_id, ws in active_connections[game_id].items():
        try:
            await ws.send_json({
                'type': 'game_update',
                'data': game.to_dict()
            })
        except:
            pass

@app.get("/api/game/{game_id}")
async def get_game_state(game_id: str):
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game.to_dict()

@app.get("/api/card/{game_id}/{user_id}")
async def get_user_card(game_id: str, user_id: int):
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    card = game.get_card_for_user(user_id)
    if not card:
        raise HTTPException(status_code=404, detail="User not in game")
    
    return {
        'card': card,
        'marked': game.get_marked_for_user(user_id)
    }

@app.post("/api/draw/{game_id}")
async def draw_number(game_id: str, admin_id: int):
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game.admin_id != admin_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    number = game.draw_number()
    if not number:
        return {'status': 'finished', 'message': 'All numbers drawn'}
    
    await broadcast_game_update(game_id)
    return {'number': number, 'total_called': len(game.called_numbers)}

@app.get("/")
async def root():
    return {
        "message": "🇪🇹 Habesha BINGO API",
        "bot": BOT_NAME,
        "username": BOT_USERNAME,
        "status": "running"
    }

# ===== RUN BOT =====

async def run_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Set it in the Render Environment variables.")
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("draw", draw_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("contact", contact_command))
    
    print(f"🤖 {BOT_NAME} (@{BOT_USERNAME}) is running...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    import threading
    
    bot_thread = threading.Thread(target=lambda: asyncio.run(run_bot()))
    bot_thread.daemon = True
    bot_thread.start()
    
    print(f"🚀 Habesha BINGO Server running on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
