import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# انوائرمنٹ ویری ایبلز لوڈ کریں
load_dotenv()

# ڈیٹا بیس کا سیٹ اپ
DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            last_redeem_date TEXT,
            referral_count INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER,
            date TEXT,
            FOREIGN KEY (referrer_id) REFERENCES users(user_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# بوٹ کا مین فنکشن
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # چینلز چیک کریں (اگر .env میں موجود ہوں)
    private_channels = os.getenv('PRIVATE_CHANNELS')
    
    if private_channels:  # اگر چینلز دیے گئے ہیں
        private_channels = [int(ch) for ch in private_channels.split(',')]
        not_member = []
        
        for channel_id in private_channels:
            try:
                member = await context.bot.get_chat_member(channel_id, user_id)
                if member.status in ['left', 'kicked']:
                    not_member.append(channel_id)
            except Exception as e:
                print(f"Error checking channel membership: {e}")
        
        if not_member:
            await update.message.reply_text(
                "⚠️ آپ کو کچھ پرائیویٹ چینلز جوائن کرنے ہوں گے۔ براہ کرم ان چینلز کو جوائن کریں اور پھر /join کمانڈ استعمال کریں۔"
            )
            return  # یوزر کو مینو پر نہیں بھیجیں گے
    
    # اگر کوئی چینلز نہیں یا یوزر ممبر ہے، تو مینو دکھائیں
    await show_menu(update, context)

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance, referral_count FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    
    if user_data:
        balance, referral_count = user_data
    else:
        # نئے یوزر کو ڈیٹا بیس میں شامل کریں
        balance = 0
        referral_count = 0
        cursor.execute(
            "INSERT INTO users (user_id, balance, referral_count) VALUES (?, ?, ?)",
            (user_id, balance, referral_count)
        )
        conn.commit()
    
    menu_text = (
        "🌟 **مینو** 🌟\n\n"
        f"💰 اکاؤنٹ بیلنس: **{balance} روپے**\n"
        f"👥 ریفرلز: **{referral_count}**\n\n"
        "🔹 **دستے یاب کمانڈز** 🔹\n"
        "/redeem - روزانہ 10 روپے ریڈیم کریں\n"
        "/myreferrals - اپنے ریفرلز دیکھیں\n"
        "/myreferrallink - اپنا ریفرل لنک حاصل کریں"
    )
    
    await update.message.reply_text(menu_text)
    conn.close()

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT last_redeem_date FROM users WHERE user_id = ?", 
        (user_id,)
    )
    user_data = cursor.fetchone()
    
    if user_data and user_data[0] == today:
        await update.message.reply_text("❌ آپ آج پہلے ہی ریڈیم کر چکے ہیں۔ کل دوبارہ کوشش کریں۔")
    else:
        cursor.execute(
            "UPDATE users SET balance = balance + 10, last_redeem_date = ? WHERE user_id = ?",
            (today, user_id)
        )
        conn.commit()
        await update.message.reply_text("🎉 مبارک ہو! آپ نے **10 روپے** کامیابی سے ریڈیم کر لیے ہیں۔")
    
    conn.close()

async def my_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT referral_count FROM users WHERE user_id = ?", (user_id,))
    referral_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT referred_id, date FROM referrals WHERE referrer_id = ?", (user_id,))
    referrals = cursor.fetchall()
    
    if referrals:
        referrals_list = "\n".join([f"▫️ User ID: {ref[0]} - تاریخ: {ref[1]}" for ref in referrals])
        text = f"👥 **کل ریفرلز:** {referral_count}\n\n{referrals_list}"
    else:
        text = f"👥 **کل ریفرلز:** {referral_count}\n\n📌 آپ کے اب تک کوئی ریفرلز نہیں ہیں۔"
    
    await update.message.reply_text(text)
    conn.close()

async def my_referral_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref{user_id}"
    
    await update.message.reply_text(
        f"🔗 **آپ کا ریفرل لنک:**\n\n{referral_link}\n\n"
        "✨ اس لنک کو شیئر کرکے ریفرلز حاصل کریں اور انعامات کمائیں!"
    )

async def handle_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text
    
    if message_text.startswith('/start ref'):
        referrer_id = int(message_text.split('ref')[1])
        
        if referrer_id != user_id:  # خود کو ریفر نہیں کر سکتے
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM referrals WHERE referrer_id = ? AND referred_id = ?",
                (referrer_id, user_id)
            )
            existing = cursor.fetchone()
            
            if not existing:
                today = datetime.now().strftime('%Y-%m-%d')
                
                cursor.execute(
                    "UPDATE users SET balance = balance + 10, referral_count = referral_count + 1 "
                    "WHERE user_id = ?", 
                    (referrer_id,)
                )
                
                cursor.execute(
                    "INSERT INTO referrals (referrer_id, referred_id, date) VALUES (?, ?, ?)",
                    (referrer_id, user_id, today)
                )
                
                conn.commit()
                
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 **نیا ریفرل!**\n\n💰 آپ کو **10 روپے** کا بونس ملا ہے!"
                    )
                except:
                    pass  # اگر ریفرر نے بوٹ کو بلاک کیا ہو تو اسے نظر انداز کریں
            
            conn.close()
    
    await start(update, context)

def main():
    init_db()
    bot_token = os.getenv('BOT_TOKEN')
    
    if not bot_token:
        raise ValueError("❌ براہ کرم .env فائل میں BOT_TOKEN سیٹ کریں")
    
    application = Application.builder().token(bot_token).build()
    
    application.add_handler(CommandHandler("start", handle_referral))
    application.add_handler(CommandHandler("join", join))
    application.add_handler(CommandHandler("myaccount", show_menu))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("myreferrals", my_referrals))
    application.add_handler(CommandHandler("myreferrallink", my_referral_link))
    
    application.run_polling()

if __name__ == "__main__":
    main()