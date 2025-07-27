import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import os
from dotenv import load_dotenv
from datetime import datetime, time

# Load environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Banner image paths
BANNERS = {
    'main_menu': 'logo.png',
    'account': 'logo.png',
    'referrals': 'logo.png',
    'settings': 'logo.png',
    'withdraw': 'logo.png'
}

# Sample data storage (replace with a proper database in production)
users_db = {}
channels_to_join = {
   # "channel1": {"id": -1001234567890, "link": "https://t.me/channel1"},  # Private channel with 
    "channel2": {"link": "https://t.me/only_possible_world"},  # Public channel with only link
}

class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.balance = 0
        self.referrals = []
        self.has_claimed_daily = False
        self.has_joined_all = False

def get_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = User(user_id)
    return users_db[user_id]

def start(update: Update, context: CallbackContext) -> None:
    user = get_user(update.effective_user.id)
    
    # Check if user has joined all required channels
    check_joined_channels(update, context, user)
    
    if user.has_joined_all:
        show_main_menu(update, context)
    else:
        show_join_channels(update, context)

def check_joined_channels(update: Update, context: CallbackContext, user: User) -> bool:
    # In a real implementation, you would check if user has joined all channels with IDs
    # This is a placeholder - actual implementation requires channel checks
    user.has_joined_all = True  # For testing, set to True
    return user.has_joined_all

def show_join_channels(update: Update, context: CallbackContext) -> None:
    keyboard = []
    
    # Add buttons for each channel
    for channel_name, channel_data in channels_to_join.items():
        keyboard.append([InlineKeyboardButton(
            f"Join {channel_name}", 
            url=channel_data["link"]
        )])
    
    # Add "Check Join" button
    keyboard.append([InlineKeyboardButton("✅ I've Joined All", callback_data='check_join')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message with banner and buttons
    try:
        with open(BANNERS['main_menu'], 'rb') as banner:
            update.message.reply_photo(
                photo=banner,
                caption="Please join all our channels to continue:",
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        update.message.reply_text(
            text="Please join all our channels to continue:",
            reply_markup=reply_markup
        )

def show_main_menu(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("💰 My Account", callback_data='my_account')],
        [InlineKeyboardButton("🎁 Daily Reward (10 Rs)", callback_data='daily_reward')],
        [InlineKeyboardButton("👥 My Referrals", callback_data='my_referrals')],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data='settings'),
            InlineKeyboardButton("💳 Withdraw", callback_data='withdraw')
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        with open(BANNERS['main_menu'], 'rb') as banner:
            if update.callback_query:
                update.callback_query.message.reply_photo(
                    photo=banner,
                    caption="Welcome to the main menu!",
                    reply_markup=reply_markup
                )
            else:
                update.message.reply_photo(
                    photo=banner,
                    caption="Welcome to the main menu!",
                    reply_markup=reply_markup
                )
    except FileNotFoundError:
        if update.callback_query:
            update.callback_query.edit_message_text(
                text="Welcome to the main menu!",
                reply_markup=reply_markup
            )
        else:
            update.message.reply_text(
                text="Welcome to the main menu!",
                reply_markup=reply_markup
            )

def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    user = get_user(query.from_user.id)
    
    if query.data == 'check_join':
        if check_joined_channels(update, context, user):
            show_main_menu(update, context)
        else:
            query.message.reply_text("You haven't joined all required channels yet!")
    
    elif query.data == 'my_account':
        show_account_info(update, context)
    
    elif query.data == 'daily_reward':
        claim_daily_reward(update, context)
    
    elif query.data == 'my_referrals':
        show_referrals_info(update, context)
    
    elif query.data == 'settings':
        show_settings(update, context)
    
    elif query.data == 'withdraw':
        show_withdraw(update, context)
    
    elif query.data == 'back_to_menu':
        show_main_menu(update, context)

def show_account_info(update: Update, context: CallbackContext) -> None:
    user = get_user(update.callback_query.from_user.id)
    
    text = (
        f"📊 Your Account Info:\n\n"
        f"💰 Balance: {user.balance} Rs\n"
        f"👥 Referrals: {len(user.referrals)}\n"
        f"🎁 Daily Reward: {'Claimed' if user.has_claimed_daily else 'Available'}"
    )
    
    try:
        with open(BANNERS['account'], 'rb') as banner:
            update.callback_query.message.reply_photo(
                photo=banner,
                caption=text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data='back_to_menu')]
                ])
            )
    except FileNotFoundError:
        update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data='back_to_menu')]
            ])
        )

def claim_daily_reward(update: Update, context: CallbackContext) -> None:
    user = get_user(update.callback_query.from_user.id)
    
    if user.has_claimed_daily:
        text = "You've already claimed your daily reward today!"
    else:
        user.balance += 10
        user.has_claimed_daily = True
        text = "🎉 You've claimed your daily 10 Rs reward!"
    
    update.callback_query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data='back_to_menu')]
        ])
    )

def show_referrals_info(update: Update, context: CallbackContext) -> None:
    user = get_user(update.callback_query.from_user.id)
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start={user.user_id}"
    
    text = (
        f"👥 Your Referrals:\n\n"
        f"Total Referrals: {len(user.referrals)}\n"
        f"Your Referral Link:\n{referral_link}"
    )
    
    try:
        with open(BANNERS['referrals'], 'rb') as banner:
            update.callback_query.message.reply_photo(
                photo=banner,
                caption=text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data='back_to_menu')]
                ])
            )
    except FileNotFoundError:
        update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data='back_to_menu')]
            ])
        )

def show_settings(update: Update, context: CallbackContext) -> None:
    text = "⚙️ Settings\n\nConfigure your account settings here."
    
    try:
        with open(BANNERS['settings'], 'rb') as banner:
            update.callback_query.message.reply_photo(
                photo=banner,
                caption=text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Change Language", callback_data='change_language')],
                    [InlineKeyboardButton("Notification Settings", callback_data='notifications')],
                    [InlineKeyboardButton("🔙 Back", callback_data='back_to_menu')]
                ])
            )
    except FileNotFoundError:
        update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Change Language", callback_data='change_language')],
                [InlineKeyboardButton("Notification Settings", callback_data='notifications')],
                [InlineKeyboardButton("🔙 Back", callback_data='back_to_menu')]
            ])
        )

def show_withdraw(update: Update, context: CallbackContext) -> None:
    user = get_user(update.callback_query.from_user.id)
    
    text = (
        f"💳 Withdraw Funds\n\n"
        f"Available Balance: {user.balance} Rs\n"
        f"Minimum Withdrawal: 100 Rs\n\n"
        f"Select withdrawal method:"
    )
    
    try:
        with open(BANNERS['withdraw'], 'rb') as banner:
            update.callback_query.message.reply_photo(
                photo=banner,
                caption=text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("JazzCash", callback_data='withdraw_jazzcash')],
                    [InlineKeyboardButton("EasyPaisa", callback_data='withdraw_easypaisa')],
                    [InlineKeyboardButton("Bank Transfer", callback_data='withdraw_bank')],
                    [InlineKeyboardButton("🔙 Back", callback_data='back_to_menu')]
                ])
            )
    except FileNotFoundError:
        update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("JazzCash", callback_data='withdraw_jazzcash')],
                [InlineKeyboardButton("EasyPaisa", callback_data='withdraw_easypaisa')],
                [InlineKeyboardButton("Bank Transfer", callback_data='withdraw_bank')],
                [InlineKeyboardButton("🔙 Back", callback_data='back_to_menu')]
            ])
        )

def handle_referral(update: Update, context: CallbackContext) -> None:
    # Check if the command has a referral parameter
    if len(context.args) > 0:
        referrer_id = int(context.args[0])
        referred_user_id = update.effective_user.id
        
        if referred_user_id != referrer_id:
            referrer = get_user(referrer_id)
            if referred_user_id not in referrer.referrals:
                referrer.referrals.append(referred_user_id)
                referrer.balance += 50  # Example: 50 Rs for each referral
                
                # Notify the referrer
                context.bot.send_message(
                    chat_id=referrer_id,
                    text=f"🎉 New referral! You got 50 Rs. Total referrals: {len(referrer.referrals)}"
                )

def reset_daily_rewards(context: CallbackContext) -> None:
    # This function would be called daily to reset the daily reward status
    for user in users_db.values():
        user.has_claimed_daily = False
    logger.info("Daily rewards have been reset for all users")

def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_click))
    
    # Add referral handler
    dispatcher.add_handler(CommandHandler("start", handle_referral, pass_args=True))

    # Set up daily job to reset rewards (runs at midnight UTC)
    job_queue = updater.job_queue
    job_queue.run_daily(reset_daily_rewards, time=time(hour=0, minute=0))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()