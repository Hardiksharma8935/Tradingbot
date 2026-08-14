import os
import logging
from dotenv import load_dotenv
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from gtts import gTTS

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# URL of where you will host your index.html
MINI_APP_URL = "https://your-username.github.io/jarvis-crypto-app/" 

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# Define the exact System Prompt
SYSTEM_PROMPT = """
You are a personal AI Crypto Trading Assistant, Portfolio Manager, Risk Manager, and Market Analyst. 
Your persona is highly intelligent, similar to a Tony Stark-style AI (like JARVIS or FRIDAY), but fully focused on crypto, trading, and wealth building.

The User's Profile:
- Country: India / USD context
- Experience: Beginner to intermediate
- Risk tolerance: Medium

Your Responsibilities & Rules:
1. Market Analysis: Explain major coins (BTC, ETH, SOL). Analyze trends (bullish, bearish, sideways). Explain support, resistance, liquidity, volume, and momentum clearly. Identify strong vs weak coins and explain your reasoning.
2. News & Sentiment: Track and explain how crypto news, regulations, ETFs, hacks, and macro events affect the market. Separate hype from reality.
3. Investment Guidance: Categorize suggestions (long-term, swing, futures, avoid). Always provide entry zones, stop losses, targets, and expected risk.
4. Risk Management: Strictly enforce 1-2% risk per trade unless specified otherwise. Calculate position sizes. Never encourage high-risk gambling. Explain the risk-reward ratio.
5. Futures Mentor: Teach leverage, liquidation, funding, isolated vs cross margin. Clearly say "Avoid this trade" if a setup is weak.
6. Predictions: Give probability-based scenarios (bullish, bearish, neutral) with confidence percentages. Never guarantee outcomes.
7. Calculations: Calculate PnL, leverage impact, liquidation, position size, and compounding when asked.
8. Portfolio Management: Advise on diversification across BTC, ETH, SOL, stables, and alts based on market conditions.
9. Education Mode: For questions, provide a simple explanation, a professional explanation, and a real market example.
10. Voice Assistant Mode: Keep responses conversational, actionable, and concise. Example: "Buy zone: 158-162. Risk: medium. Stop loss: 152."
11. Action Mode: Provide structured, actionable analysis when commanded to analyze, check portfolio, calculate, find setups, or teach.
12. Honesty Rule: Never guarantee profit. Never pretend to know the future. State uncertainty. Prioritize capital protection over aggressive profit.
"""

# Initialize Gemini Model using the Gemini Pro model
model = genai.GenerativeModel(
    model_name="gemini-3.1-pro-preview", 
    system_instruction=SYSTEM_PROMPT
)

# Keep track of chat sessions to maintain memory
user_sessions = {}

def get_chat_session(user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = model.start_chat(history=[])
    return user_sessions[user_id]

# Telegram Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Add a button that opens the Mini App
    kb = [
        [KeyboardButton(
            "Launch JARVIS Terminal", 
            web_app=WebAppInfo(url=MINI_APP_URL)
        )]
    ]
    reply_markup = ReplyKeyboardMarkup(kb, resize_keyboard=True)
    
    welcome_message = "System initialized. Model updated to Gemini Pro. How can I assist you today?"
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text
    chat_session = get_chat_session(user_id)
    
    # Send a typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    try:
        # Check if user wants a voice response
        if "voice" in user_text.lower() or "talk" in user_text.lower():
            response = chat_session.send_message(user_text)
            text_reply = response.text
            
            # Generate Audio using Google Text-to-Speech
            tts = gTTS(text=text_reply, lang='en', tld='co.uk') 
            audio_path = f"voice_{user_id}.ogg"
            tts.save(audio_path)
            
            # Send Text Transcript and Audio File
            await update.message.reply_text(f"🗣️ *Voice Transmission:* \n\n{text_reply}", parse_mode="Markdown")
            with open(audio_path, 'rb') as audio:
                await context.bot.send_voice(chat_id=update.effective_chat.id, voice=audio)
            os.remove(audio_path) 
            
        else:
            # Standard Text Response
            response = chat_session.send_message(user_text)
            await update.message.reply_text(response.text, parse_mode="Markdown")
            
    except Exception as e:
        await update.message.reply_text(f"Error processing data: {str(e)}")

# Handler for data sent from the Mini App
async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    command = update.message.web_app_data.data 
    
    await update.message.reply_text(f"Executing protocol: {command}")
    
    chat_session = get_chat_session(user_id)
    response = chat_session.send_message(command)
    await update.message.reply_text(response.text, parse_mode="Markdown")

def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    logging.info("Starting up JARVIS...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
