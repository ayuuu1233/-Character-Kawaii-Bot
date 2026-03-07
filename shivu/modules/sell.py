from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as app, user_collection
import random

# ---------------- EMOJIS & RARITY ---------------- #
ANIMATED_EMOJIS = ['✨', '🎉', '💫', '🌟', '🔥', '🌀', '🎇', '💖', '🎆', '💥', '🌈']
SUCCESS_EMOJIS = ['✅', '✔️', '🆗', '🎯', '🏅']
CANCEL_EMOJIS = ['❌', '🚫', '⚠️', '🔴', '🚷']

RARITY_EMOJIS = {
    '𝘾𝙊𝙈𝙈𝙊𝙉': ('⚪️', 'Common'),
    '𝙈𝙀𝘿𝙄𝙐𝙈': ('🔵', 'Medium'),
    '𝘾𝙃𝙄𝘽𝙄': ('👶', 'Chibi'),
    '𝙍𝘼𝙍𝙀': ('🟠', 'Rare'),
    '𝙇𝙀𝙂𝙀𝙉𝘿𝘼𝙍𝙔': ('🟡', 'Legendary'),
    '𝙀𝙓𝘾𝙇𝙐𝙎𝙄𝙑𝙀': ('💮', 'Exclusive'),
    '𝙋𝙍𝙀𝙈𝙄𝙐𝙈': ('🫧', 'Premium'),
    '𝙇𝙄𝙈𝙄𝙏𝙀𝘿 𝙀𝘿𝙄𝙏𝙄𝙊𝙉': ('🔮', 'Limited Edition'),
    '𝙀𝙓𝙊𝙏𝙄𝘾': ('🌸', 'Exotic'),
    '𝘼𝙎𝙏𝙍𝘼𝙇': ('🎐', 'Astral'),
    '𝙑𝘼𝙇𝙀𝙉𝙏𝙄𝙉𝙀': ('💞', 'Valentine')
}

# Initialize user_data storage
if not hasattr(app, "user_data"):
    app.user_data = {}
app.user_data["buy_confirmations"] = {}

# ---------------- CHARACTER DATA ---------------- #
# Example function: replace with your real DB/API
async def fetch_character_data(char_id):
    characters = {
        "1": {"id": 1, "name": "Mikasa Ackerman", "anime": "Attack on Titan", "rarity": "𝙍𝘼𝙍𝙀", "img_url": "https://i.imgur.com/example.png"},
        "2": {"id": 2, "name": "Naruto Uzumaki", "anime": "Naruto", "rarity": "𝙈𝙀𝘿𝙄𝙐𝙈", "img_url": "https://i.imgur.com/example2.png"},
        # Add more characters as needed
    }
    return characters.get(str(char_id))

# ---------------- COST CALCULATION ---------------- #
def calculate_buy_cost(rarity: str) -> int:
    cost_values = {
        '𝘾𝙊𝙈𝙈𝙊𝙉': 1000,
        '𝙈𝙀𝘿𝙄𝙐𝙈': 2000,
        '𝘾𝙃𝙄𝘽𝙄': 5000,
        '𝙍𝘼𝙍𝙀': 2500,
        '𝙇𝙀𝙂𝙀𝙉𝘿𝘼𝙍𝙔': 15000,
        '𝙀𝙓𝘾𝙇𝙐𝙎𝙄𝙑𝙀': 10000,
        '𝙋𝙍𝙀𝙈𝙄𝙐𝙈': 12500,
        '𝙇𝙄𝙈𝙄𝙏𝙀𝘿 𝙀𝘿𝙄𝙏𝙄𝙊𝙉': 20000,
        '𝙀𝙓𝙊𝙏𝙄𝘾': 15000,
        '𝘼𝙎𝙏𝙍𝘼𝙇': 25000,
        '𝙑𝘼𝙇𝙀𝙉𝙏𝙄𝙉𝙀': 30000
    }
    return cost_values.get(rarity, 1000)

# ---------------- /BUY COMMAND ---------------- #
@app.on_message(filters.command("buy"))
async def buy(client: Client, message):
    user_id = message.from_user.id

    # Check if command has a character ID
    if len(message.command) < 2:
        return await message.reply_text(
            f'{random.choice(CANCEL_EMOJIS)} **Invalid usage!**\n'
            f'Use `/buy (waifu_id)`\n**Example:** `/buy 1`'
        )

    character_id = message.command[1]

    # Fetch user from DB
    user = await user_collection.find_one({'id': user_id})
    if not user:
        return await message.reply_text('😔 **You need to start your collection first!**')

    # Check if already owns
    if any(str(c.get('id')) == character_id for c in user.get('characters', [])):
        return await message.reply_text('🤔 **You already own this character!**')

    # Fetch character
    character = await fetch_character_data(character_id)
    if not character:
        return await message.reply_text('😞 **Character not found.**')

    rarity_emoji, rarity_display = RARITY_EMOJIS.get(character.get('rarity', '𝘾𝙊𝙈𝙈𝙊𝙉'), ('', 'Common'))
    cost = calculate_buy_cost(character.get('rarity', '𝘾𝙊𝙈𝙈𝙊𝙉'))

    # Send confirmation
    confirmation_message = await message.reply_photo(
        photo=character['img_url'],
        caption=(
            f"🛍️ **Confirm Your Purchase** 🛍️\n\n"
            f"🫧 **Name:** `{character.get('name', 'Unknown')}`\n"
            f"⛩️ **Anime:** `{character.get('anime', 'Unknown')}`\n"
            f"🥂 **Rarity:** {rarity_emoji} `{rarity_display}`\n"
            f"💰 **Cost:** `{cost} tokens`\n\n"
            "⚜️ **Choose an option:**"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🟢 Confirm", callback_data=f"buy_yes_{character_id}_{cost}"),
                InlineKeyboardButton("🔴 Cancel", callback_data=f"buy_no_{character_id}")
            ]
        ])
    )

    # Store confirmation
    app.user_data["buy_confirmations"][confirmation_message.message_id] = character_id

# ---------------- CALLBACK HANDLER ---------------- #
@app.on_callback_query(filters.regex(r"^buy_(yes|no)_.+"))
async def handle_buy_confirmation(client: Client, callback_query):
    parts = callback_query.data.split("_", 3)
    if len(parts) < 3:
        return await callback_query.answer("Invalid data received.")
    
    action = parts[1]
    character_id = parts[2]
    cost = int(parts[3]) if action == "yes" else 0
    user_id = callback_query.from_user.id

    user = await user_collection.find_one({'id': user_id})
    if not user:
        return await callback_query.answer("😔 **Start your collection first!**")

    if action == "yes":
        if user.get('tokens', 0) < cost:
            return await callback_query.answer("❌ **Not enough tokens!**")
        
        character = await fetch_character_data(character_id)
        if not character:
            return await callback_query.answer("😞 **Character not found.**")

        await user_collection.update_one(
            {'id': user_id},
            {'$push': {'characters': character}, '$inc': {'tokens': -cost}}
        )

        await callback_query.message.edit_caption(
            caption=(
                f"{random.choice(SUCCESS_EMOJIS)} {random.choice(ANIMATED_EMOJIS)}\n"
                f"**Congratulations!** You bought `{character.get('name', 'Unknown')}` "
                f"for `{cost}` tokens."
            ),
            reply_markup=None
        )

    elif action == "no":
        await callback_query.message.edit_caption(
            caption=f"{random.choice(CANCEL_EMOJIS)} **Purchase cancelled.**",
            reply_markup=None
        )

    await callback_query.answer()  # remove "loading" animation
