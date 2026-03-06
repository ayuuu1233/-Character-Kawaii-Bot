import random
import asyncio
import time
import os
import requests
from PIL import Image, ImageFilter
from pyrogram import filters
from shivu import shivuu as app, user_collection, collection

active_games = {}
spam_control = {}

BLUR_LEVELS = [20, 10, 4, 0]

REWARD_TABLE = {
    "easy": (300,600),
    "medium": (600,1000),
    "hard": (1000,1500)
}

def blur_image(input_path, output_path, blur):
    img = Image.open(input_path)
    img = img.filter(ImageFilter.GaussianBlur(blur))
    img.save(output_path)

async def download_image(url, path):
    r = requests.get(url)
    with open(path,"wb") as f:
        f.write(r.content)

@app.on_message(filters.command("guess") & filters.group)
async def start_guess(client, message):

    chat_id = message.chat.id

    if chat_id in active_games:
        await message.reply_text("🎮 A guess game is already running in this group!")
        return

    args = message.command[1:] if len(message.command) > 1 else []

    category = None
    difficulty = "medium"

    for arg in args:
        if arg.lower() in ["anime","game","movie"]:
            category = arg.lower()
        if arg.lower() in ["easy","medium","hard"]:
            difficulty = arg.lower()

    query = {"category": category} if category else {}

    characters = await collection.find(query).to_list(length=None)

    if not characters:
        await message.reply_text("❌ No characters found.")
        return

    char = random.choice(characters)

    name = char["name"]
    img_url = char["img_url"]

    file_original = f"guess_{chat_id}.jpg"

    await download_image(img_url, file_original)

    blur_file = f"blur_{chat_id}.jpg"

    blur_image(file_original, blur_file, BLUR_LEVELS[0])

    msg = await message.reply_photo(
        blur_file,
        caption=f"""
🎮 **Guess The Character**

Mode: {category or "mixed"}
Difficulty: {difficulty}

Reply with the character name.

⏳ 60 seconds time
💡 2 hints will appear
"""
    )

    active_games[chat_id] = {
        "answer": name.lower(),
        "name": name,
        "difficulty": difficulty,
        "msg": msg
    }

    await asyncio.sleep(20)

    if chat_id not in active_games:
        return

    blur_image(file_original, blur_file, BLUR_LEVELS[1])

    await msg.edit_media(
        media=msg.photo,
    )

    hint = f"{name[0]}{'*'*(len(name)-1)}"

    await message.reply_text(f"💡 Hint 1: `{hint}`")

    await asyncio.sleep(20)

    if chat_id not in active_games:
        return

    blur_image(file_original, blur_file, BLUR_LEVELS[2])

    await message.reply_text(
        f"💡 Hint 2: Name length is **{len(name)}** letters"
    )

    await asyncio.sleep(20)

    if chat_id in active_games:

        await message.reply_text(
            f"⏳ Time's up!\n\nCorrect Answer: **{name}**"
        )

        del active_games[chat_id]


@app.on_message(filters.group & ~filters.command(["guess"]))
async def guess_check(client, message):

    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id not in active_games:
        return

    if not message.text:
        return

    now = time.time()

    if user_id in spam_control and now - spam_control[user_id] < 3:
        return

    spam_control[user_id] = now

    game = active_games[chat_id]

    if message.text.lower() != game["answer"]:
        return

    difficulty = game["difficulty"]

    reward_range = REWARD_TABLE[difficulty]

    reward = random.randint(reward_range[0], reward_range[1])

    jackpot = False

    if random.randint(1,25) == 1:
        reward += 3000
        jackpot = True

    lootbox = False

    if random.randint(1,10) == 1:
        lootbox = True

    await user_collection.update_one(
        {"id": user_id},
        {"$inc":{"balance":reward}},
        upsert=True
    )

    stats = await user_collection.find_one({"id":user_id})

    wins = stats.get("wins",0) + 1
    games = stats.get("games",0) + 1

    await user_collection.update_one(
        {"id":user_id},
        {"$set":{"wins":wins,"games":games}}
    )

    text = f"""
🎉 **{message.from_user.first_name} guessed correctly!**

💰 Reward: {reward} coins
🏆 Total Wins: {wins}
"""

    if jackpot:
        text += "\n🎁 JACKPOT BONUS!"

    if lootbox:
        text += "\n📦 You received a **Loot Box!**"

        await user_collection.update_one(
            {"id":user_id},
            {"$inc":{"lootbox":1}}
        )

    await message.reply_text(text)

    del active_games[chat_id]


@app.on_message(filters.command("guessleaderboard"))
async def leaderboard(client, message):

    users = user_collection.find().sort("wins",-1).limit(10)

    text = "🏆 **Guess Leaderboard**\n\n"

    rank = 1

    async for u in users:
        text += f"{rank}. {u.get('id')} — {u.get('wins',0)} wins\n"
        rank += 1

    await message.reply_text(text)


@app.on_message(filters.command("guessglobal"))
async def global_rank(client, message):

    users = user_collection.find().sort("wins",-1).limit(10)

    text = "🌍 **Global Guess Ranking**\n\n"

    rank = 1

    async for u in users:
        text += f"{rank}. {u.get('id')} — {u.get('wins',0)} wins\n"
        rank += 1

    await message.reply_text(text)


@app.on_message(filters.command("guessstats"))
async def stats(client, message):

    user = await user_collection.find_one({"id":message.from_user.id})

    if not user:
        await message.reply_text("You haven't played yet.")
        return

    text = f"""
📊 **Your Guess Stats**

🎮 Games Played: {user.get('games',0)}
🏆 Wins: {user.get('wins',0)}
📦 Loot Boxes: {user.get('lootbox',0)}
"""

    await message.reply_text(text)
