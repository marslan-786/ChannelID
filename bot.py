from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ایک لسٹ میں ان چینلز کی جانچ کرو جن میں بوٹ ایڈمن ہے
# یہاں ہم فرض کرتے ہیں کہ تمہارا بوٹ خود جانتا ہے کہ وہ کن چینلز میں ایڈمن ہے
# (اگر نہیں تو ہم bot.get_my_chats() نہیں لے سکتے، تو تمہیں خود وہ چینلز یہاں فکس کرنے ہوں گے)

CHANNELS = [
    "@only_possible_world",
    "@QayoomX_kami",
]

async def getchannels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lines = []
    for ch in CHANNELS:
        # یہاں ہم فرض کر رہے ہیں کہ چینل یوزرنیم سے ہم اس کا ID نکال سکتے ہیں
        try:
            chat = await context.bot.get_chat(ch)
            lines.append(f"{chat.username} : {chat.id}")
        except Exception as e:
            lines.append(f"{ch} : ERROR - {str(e)}")

    # فائل بنائیں
    filename = "channels_list.txt"
    with open(filename, "w") as f:
        f.write("\n".join(lines))

    # فائل بھیجیں
    with open(filename, "rb") as f:
        await context.bot.send_document(chat_id=chat_id, document=f, filename=filename)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("getchannels", getchannels))

    print("Bot is running...")
    app.run_polling()