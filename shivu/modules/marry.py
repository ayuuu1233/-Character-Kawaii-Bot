import asyncio
import random
import time
from datetime import datetime

from pyrogram import filters
from pyrogram.types import Message
from shivu import shivuu as bot
from shivu import user_collection, collection

# ------------------------------
# GLOBAL SYSTEMS
# ------------------------------

cooldowns = {}
roll_streaks = {}
daily_bonus = {}

STREAK_REWARDS = {
    5: "🌟 Rare Love Blessing",
    10: "💎 Legendary Love Bonus",
    20: "👑 Ultimate Marriage Master"
}

RARITIES = ["⚪️ Common", "🔵 Medium", "🟠 Rare", "🟡 Legendary"]

# ------------------------------
# MESSAGE SYSTEM
# ------------------------------

def congrats_message(user, char):
    partner = f"\n💑 Best Couple: {char.get('partner')}" if char.get("partner") else ""

    return (
        f"💍 **Marriage Successful!**\n\n"
        f"🎉 {user} married **{char['name']}**\n"
        f"🏯 Anime: **{char['anime']}**\n"
        f"⭐ Rarity: {char['rarity']}"
        f"{partner}"
    )


def rejection_message(user):
    msgs = [
        f"💔 {user}, your proposal got rejected.",
        f"👻 {user}, your soulmate vanished into another dimension.",
        f"🥀 {user}, love wasn't destined today."
    ]
    return random.choice(msgs)


def cooldown_msg(seconds):
    emojis = ["⏳", "⌛", "🕒"]
    return f"{random.choice(emojis)} Wait **{seconds}s** before proposing again."


def streak_msg(user_id):
    streak = roll_streaks.get(user_id, 0)
    if streak in STREAK_REWARDS:
        return f"🔥 Streak {streak}! {STREAK_REWARDS[streak]}"
    return None


# ------------------------------
# DATABASE HELPERS
# ------------------------------

async def get_user_char_ids(user_id):
    user = await user_collection.find_one({"id": user_id}) or {}
    return [c["id"] for c in user.get("characters", [])]


async def get_random_character(user_id):

    owned = await get_user_char_ids(user_id)

    pipeline = [
        {
            "$match": {
                "rarity": {"$in": RARITIES},
                "id": {"$nin": owned}
            }
        },
        {"$sample": {"size": 1}}
    ]

    cursor = collection.aggregate(pipeline)
    data = await cursor.to_list(length=1)

    return data[0] if data else None


async def add_character(user_id, char):

    await user_collection.update_one(
        {"id": user_id},
        {"$push": {"characters": char}},
        upsert=True
    )


# ------------------------------
# SPECIAL SYSTEMS
# ------------------------------

def ultra_rare_trigger():
    return random.randint(1, 200) == 1


def jackpot_trigger():
    return random.randint(1, 100) == 1


def daily_bonus_trigger(user_id):

    today = datetime.utcnow().date()

    if daily_bonus.get(user_id) != today:
        daily_bonus[user_id] = today
        return True

    return False


# ------------------------------
# MAIN COMMAND
# ------------------------------

@bot.on_message(filters.command("marry"))
async def marry_command(_, message: Message):

    user = message.from_user
    user_id = user.id
    mention = user.mention
    chat_id = message.chat.id

    now = time.time()

    # ------------------------------
    # COOLDOWN
    # ------------------------------

    if user_id in cooldowns:

        diff = now - cooldowns[user_id]

        if diff < 60:
            return await message.reply_text(
                cooldown_msg(int(60 - diff)),
                quote=True
            )

    cooldowns[user_id] = now

    await message.reply_text("🎲 Rolling love dice...")

    dice = await bot.send_dice(chat_id)
    value = dice.dice.value

    # ------------------------------
    # FAILURE
    # ------------------------------

    if value not in [1, 6]:

        roll_streaks[user_id] = 0

        return await message.reply_text(
            rejection_message(mention)
        )

    # ------------------------------
    # SUCCESS
    # ------------------------------

    char = await get_random_character(user_id)

    if not char:
        return await message.reply_text(
            "🌪 No more unique characters left!"
        )

    await add_character(user_id, char)

    roll_streaks[user_id] = roll_streaks.get(user_id, 0) + 1

    caption = congrats_message(mention, char)

    await message.reply_photo(
        photo=char["img_url"],
        caption=caption
    )

    # ------------------------------
    # STREAK BONUS
    # ------------------------------

    s_msg = streak_msg(user_id)

    if s_msg:
        await message.reply_text(s_msg)

    # ------------------------------
    # DAILY BONUS
    # ------------------------------

    if daily_bonus_trigger(user_id):

        await message.reply_text(
            "🎁 Daily Love Bonus Received!"
        )

    # ------------------------------
    # ULTRA RARE DROP
    # ------------------------------

    if ultra_rare_trigger():

        char2 = await get_random_character(user_id)

        if char2:
            await add_character(user_id, char2)

            await message.reply_photo(
                photo=char2["img_url"],
                caption="👑 **ULTRA RARE BONUS WAIFU!**"
            )

    # ------------------------------
    # JACKPOT
    # ------------------------------

    if jackpot_trigger():

        for _ in range(2):

            bonus = await get_random_character(user_id)

            if bonus:
                await add_character(user_id, bonus)

                await message.reply_photo(
                    photo=bonus["img_url"],
                    caption="🎰 **LOVE JACKPOT BONUS!**"
                )
