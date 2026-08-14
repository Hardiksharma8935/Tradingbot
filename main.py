import os
import logging
from dotenv import load_dotenv
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
from gtts import gTTS

# Load variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# APNA GITHUB PAGES URL YAHAN DAALO
MINI_APP_URL = "[https://hardiksharma8935.github.io/tradingbot/](https://hardiksharma8935.github.io/tradingbot/)" 

# Initialize Groq
client = Groq(api_key=GROQ_API_KEY)

# Jarvis AI Persona
SYSTEM_PROMPT = """
You are JARVIS, an advanced AI Crypto Trading Assistant.
Your core tasks: Market Analysis, Risk Management, Futures Setup, and Portfolio Tracking.
Be concise, professional, and act like Tony Stark's AI. Keep responses actionable.
Never guarantee profits. Enforce strict risk management (1-2% risk).
"""

# Memory management (Taki bot purani baatein yaad rakhe)
user_memory = {}

def get_history(user_id):
    if user_id not in user_memory:
        user_memory[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return user_memory[user_id]

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[KeyboardButton("Launch JARVIS Terminal", web_app=WebAppInfo(url=MINI_APP_URL))]]
    reply_markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    await update.message.reply_text("System initialized. Groq AI Online. How can I help you boss?", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    try:
        # Load memory and add new message
        history = get_history(user_id)
        history.append({"role": "user", "content": user_text})
        
        # Keep memory size limited to last 10 messages so it doesn't crash
        if len(history) > 11: 
            history = [history[0]] + history[-10:]

        # Get response from Groq AI
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=history,
            temperature=0.6,
            max_tokens=1024
        )
        
        reply_text = completion.choices[0].message.content
        history.append({"role": "assistant", "content": reply_text})
        
        # Voice Mode Check
        if "voice" in user_text.lower() or "talk" in user_text.lower():
            # Voice processing
            tts = gTTS(text=reply_text, lang='en', tld='co.uk')
            audio_path = f"voice_{user_id}.ogg"
            tts.save(audio_path)
            
            await update.message.reply_text(f"🗣️ *JARVIS Voice Mode:*\n\n{reply_text}", parse_mode="Markdown")
            with open(audio_path, 'rb') as audio:
                await context.bot.send_voice(chat_id=update.effective_chat.id, voice=audio)
            os.remove(audio_path)
        else:
            # Normal text reply
            await update.message.reply_text(reply_text, parse_mode="Markdown")
            
    except Exception as e:
        await update.message.reply_text(f"Error processing via Groq: {str(e)}")

async def handle_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.web_app_data.data
    update.message.text = command 
    await handle_message(update, context)

def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp))

    logging.info("Starting Groq AI JARVIS...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
