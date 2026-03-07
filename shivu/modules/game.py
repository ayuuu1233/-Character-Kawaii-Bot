import random
import asyncio
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters
from telegram.helpers import mention_html

from shivu import user_collection, collection, application


active_scramble_games = {}
scramble_leaderboard = {}

ALLOWED_GROUP_ID = -1002104939708
SUPPORT_GROUP_URL = "https://t.me/dynamic_gangs"


# ---------------- FETCH CHARACTER ---------------- #

async def get_random_character():
    try:
        pipeline = [{'$sample': {'size': 1}}]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=1)
        return characters[0] if characters else None
    except Exception as e:
        print("Character fetch error:", e)
        return None


# ---------------- SCRAMBLE NAME ---------------- #

def scramble_name(name):

    if len(name) <= 2:
        return name

    name_list = list(name)
    random.shuffle(name_list)
    return "".join(name_list)


# ---------------- GENERATE HINT ---------------- #

def generate_hint(name, reveal):

    hint = ""
    reveal_index = random.sample(range(len(name)), reveal)

    for i, char in enumerate(name):

        if i in reveal_index:
            hint += char
        else:
            hint += "_"

    return hint


# ---------------- AUTO END GAME ---------------- #

async def auto_end_game(user_id, chat_id, context):

    await asyncio.sleep(120)

    if user_id in active_scramble_games:

        del active_scramble_games[user_id]

        try:
            await context.bot.send_message(
                chat_id,
                "⌛ Game ended due to inactivity."
            )
        except:
            pass


# ---------------- START GAME ---------------- #

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = user.id
    chat_id = update.effective_chat.id
    user_mention = mention_html(user_id, user.first_name)

    if chat_id != ALLOWED_GROUP_ID:

        keyboard = [[InlineKeyboardButton("Join Support Group", url=SUPPORT_GROUP_URL)]]

        await update.message.reply_text(
            f"⚠️ {user_mention} This game only works in our support group.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )

        return


    if user_id in active_scramble_games:

        await update.message.reply_text(
            "⚠️ You already have an active game!"
        )

        return


    character = await get_random_character()

    if not character:

        await update.message.reply_text("⚠️ Character database error.")
        return


    name = character["name"]
    scrambled = scramble_name(name)

    active_scramble_games[user_id] = {

        "original": name.lower(),
        "scrambled": scrambled,
        "attempts": 5,
        "hints": 0,
        "img": character["img_url"],
        "start_time": datetime.utcnow(),
        "last_guess": datetime.utcnow()
    }

    asyncio.create_task(auto_end_game(user_id, chat_id, context))

    await update.message.reply_text(

        f"🎮 <b>SCRAMBLE GAME STARTED</b>\n\n"
        f"Unscramble this character name:\n\n"
        f"🔤 <b>{scrambled}</b>\n\n"
        f"Attempts: <b>5</b>\n"
        f"Use /hint for help\n"
        f"Use /endgame to quit",

        parse_mode=ParseMode.HTML
    )


# ---------------- HINT ---------------- #

async def hint(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in active_scramble_games:

        await update.message.reply_text("❌ No active game.")
        return


    game = active_scramble_games[user_id]

    if game["hints"] >= 2:

        await update.message.reply_text("⚠️ No hints left!")
        return


    game["hints"] += 1

    hint_text = generate_hint(game["original"], game["hints"] + 1)

    await update.message.reply_text(

        f"💡 Hint:\n\n{hint_text.upper()}\n\n"
        f"Hints left: {2 - game['hints']}"
    )


# ---------------- END GAME ---------------- #

async def endgame(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in active_scramble_games:

        await update.message.reply_text("❌ No game running.")
        return


    del active_scramble_games[user_id]

    await update.message.reply_text("🚪 Game ended.")


# ---------------- GUESS HANDLER ---------------- #

async def guess_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = user.id

    if user_id not in active_scramble_games:
        return

    guess = update.message.text.lower().strip()

    game = active_scramble_games[user_id]

    now = datetime.utcnow()

    if (now - game["last_guess"]).seconds < 2:
        return

    game["last_guess"] = now

    if guess == game["original"]:

        time_taken = (now - game["start_time"]).seconds

        reward = 1

        if random.randint(1, 10) == 5:
            reward = 3

        if time_taken < 10:
            reward += 1

        img = game["img"]

        for i in range(reward):

            await user_collection.update_one(
                {"id": user_id},
                {"$push": {"collection": {"name": game["original"].title(), "img_url": img}}},
                upsert=True
            )

        scramble_leaderboard[user_id] = scramble_leaderboard.get(user_id, 0) + 1

        del active_scramble_games[user_id]

        await update.message.reply_photo(

            img,

            caption=

            f"🎉 <b>Correct!</b>\n\n"
            f"Character: <b>{game['original'].title()}</b>\n"
            f"Reward: <b>{reward} character(s)</b>",

            parse_mode=ParseMode.HTML
        )

        return


    game["attempts"] -= 1

    if game["attempts"] <= 0:

        answer = game["original"]

        del active_scramble_games[user_id]

        await update.message.reply_text(

            f"❌ Game Over\n\nAnswer was: <b>{answer.title()}</b>",
            parse_mode=ParseMode.HTML
        )

        return


    await update.message.reply_text(

        f"❌ Wrong guess!\n"
        f"Attempts left: {game['attempts']}"
    )


# ---------------- LEADERBOARD ---------------- #

async def scramble_top(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not scramble_leaderboard:

        await update.message.reply_text("No players yet.")
        return


    sorted_players = sorted(scramble_leaderboard.items(), key=lambda x: x[1], reverse=True)

    text = "🏆 <b>SCRAMBLE LEADERBOARD</b>\n\n"

    for i, (uid, score) in enumerate(sorted_players[:10], start=1):

        text += f"{i}. <a href='tg://user?id={uid}'>Player</a> — {score}\n"

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


# ---------------- BATTLE MODE ---------------- #

async def scramble_battle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    character = await get_random_character()

    if not character:
        return

    name = character["name"]
    scrambled = scramble_name(name)

    context.chat_data["battle_answer"] = name.lower()
    context.chat_data["battle_img"] = character["img_url"]

    await update.message.reply_text(

        f"⚔ <b>SCRAMBLE BATTLE</b>\n\n"
        f"First person to guess wins!\n\n"
        f"<b>{scrambled}</b>",

        parse_mode=ParseMode.HTML
    )


async def battle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if "battle_answer" not in context.chat_data:
        return

    guess = update.message.text.lower()

    if guess == context.chat_data["battle_answer"]:

        img = context.chat_data["battle_img"]

        del context.chat_data["battle_answer"]

        await update.message.reply_photo(

            img,

            caption=f"🏆 {update.effective_user.first_name} won the scramble battle!"
        )


# ---------------- HANDLERS ---------------- #

application.add_handler(CommandHandler("startgame", start_game))
application.add_handler(CommandHandler("hint", hint))
application.add_handler(CommandHandler("endgame", endgame))
application.add_handler(CommandHandler("scrambletop", scramble_top))
application.add_handler(CommandHandler("scramblebattle", scramble_battle))

application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guess_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, battle_guess))
