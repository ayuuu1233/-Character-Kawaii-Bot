import asyncio
import random
from html import escape 
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from shivu import application, PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID, OWNER_ID

# Database setup
user_collection = db['total_pm_users']
sudo_user_ids = [5158013355] 

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username
    args = context.args
    referring_user_id = None

    # Animation Logic (Emojis)
    if update.effective_chat.type == "private":
        emojis = ["✨", "🚀", "🎉"]
        for emoji in emojis:
            msg = await update.message.reply_text(emoji)
            await asyncio.sleep(0.5)
            await msg.delete()

    # User Registration & Referral
    user_data = await user_collection.find_one({"id": user_id})
    if args and args[0].startswith('r_'):
        referring_user_id = int(args[0][2:])

    if user_data is None:
        await user_collection.insert_one({"id": user_id, "first_name": first_name, "username": username, "tokens": 500, "characters": []})
        if referring_user_id:
            await user_collection.update_one({"id": referring_user_id}, {"$inc": {"tokens": 1000}})
        await context.bot.send_message(chat_id=GROUP_ID, text=f"🫧 #ɴᴇᴡ_ᴜsᴇʀ: {first_name}", parse_mode='HTML')

    # Main Menu UI
    bot_name = "ᴄʜᴧʀᴧᴄᴛєʀ-ᴋᴧᴡᴧɪɪ-ʙσᴛ" 
    caption = f"✨ Kση'ηɪᴄʜɪᴡᴧ {first_name}!\n\nᴡєʟᴄσϻє ᴛσ {bot_name}\n━━━━━━━━━━━━━━━━━━━━\n❖ I spawn characters every 100 messages.\n❖ Add me to your group to start catching!\n━━━━━━━━━━━━━━━━━━━━"

    keyboard = [
        [InlineKeyboardButton("✜ ᴧᴅᴅ ϻє ɪη ʏσυʀ ɢʀσυᴘ ✜", url=f'https://t.me/{BOT_USERNAME}?startgroup=new')],
        [InlineKeyboardButton("˹ sυᴘᴘσʀᴛ ˼", url=f'https://t.me/{SUPPORT_CHAT}'),
         InlineKeyboardButton("˹ ᴜᴘᴅᴧᴛєs ˼", url=f'https://t.me/{UPDATE_CHAT}')],
        [InlineKeyboardButton("✧ ʜᴇʟᴘ ✧", callback_data='help')]
    ]
    
    photo_url = random.choice(PHOTO_URL)
    if update.effective_chat.type == "private":
        await context.bot.send_photo(chat_id=user_id, photo=photo_url, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    else:
        await update.message.reply_photo(photo=photo_url, caption="I'm alive! Connect in PM for details.", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'help':
        help_keyboard = [
            [InlineKeyboardButton("Basic Commands", callback_data='basic')],
            [InlineKeyboardButton("Game Commands", callback_data='game')],
            [InlineKeyboardButton("⤾ Back", callback_data='back')]
        ]
        await query.edit_message_caption(caption="Choose a category to explore commands:", reply_markup=InlineKeyboardMarkup(help_keyboard))

    elif query.data == 'basic':
        basic_text = """
***➲ ʙᴀsɪᴄ ᴄᴏᴍᴍᴀɴᴅs:***
◈ /guess ➵ Character guess (In Group)
◈ /harem ➵ See your collection
◈ /fav ➵ Make a character favourite
◈ /trade ➵ Trade characters
◈ /gift ➵ Gift to another user
◈ /changetime ➵ Change spawn time
◈ /status ➵ Check bot status
"""
        await query.edit_message_caption(caption=basic_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⤾ Back", callback_data='help')]]), parse_mode='markdown')

    elif query.data == 'game':
        game_text = """
***➲ ɢᴀᴍᴇ ᴄᴏᴍᴍᴀɴᴅs:***
◉ /propose ➸ Propose a character
◉ /fight ➸ Fight Sukuna v/s Gojo
◉ /roll ➸ Roll for random character
◉ /tokens ➸ View your tokens
◉ /bal ➸ Check your balance
◉ /quiz ➸ Anime quiz
"""
        await query.edit_message_caption(caption=game_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⤾ Back", callback_data='help')]]), parse_mode='markdown')

    elif query.data == 'back':
        # Wapis main menu par jaane ka logic
        bot_name = "ᴄʜᴧʀᴧᴄᴛєʀ-ᴋᴧᴡᴧɪɪ-ʙσᴛ"
        caption = f"✨ Welcome back!\n\nᴛσ {bot_name}\n━━━━━━━━━━━━━━━━━━━━\n❖ Use /guess to collect characters.\n━━━━━━━━━━━━━━━━━━━━"
        keyboard = [
            [InlineKeyboardButton("✜ ᴧᴅᴅ ϻє ɪη ʏσυʀ ɢʀσυᴘ ✜", url=f'https://t.me/{BOT_USERNAME}?startgroup=new')],
            [InlineKeyboardButton("✧ ʜᴇʟᴘ ✧", callback_data='help')]
        ]
        await query.edit_message_caption(caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

# Handlers setup
application.add_handler(CommandHandler('start', start, block=False))
application.add_handler(CallbackQueryHandler(button, pattern='^help$|^basic$|^game$|^back$', block=False))
