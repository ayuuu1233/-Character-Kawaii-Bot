import time
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
    InputMediaPhoto
)

from shivu import shivuu as app, user_collection, collection

trade_data = {}
pagination_state = {}
cooldown = {}


# --------------------------------
# FORTRADE COMMAND
# --------------------------------

@app.on_message(filters.command("fortrade"))
async def fortrade_command(client: Client, message: Message):

    user_id = message.from_user.id

    # Anti spam cooldown
    if user_id in cooldown and time.time() - cooldown[user_id] < 5:
        await message.reply_text("⏳ Wait a few seconds before using trade again.")
        return

    cooldown[user_id] = time.time()

    if len(message.command) != 3:
        await message.reply_text("Usage:\n/fortrade <find_character_id> <your_character_id>")
        return

    find_id = message.command[1]
    own_id = message.command[2]

    find_character = await collection.find_one({"id": find_id})
    own_character = await collection.find_one({"id": own_id})

    if not find_character or not own_character:
        await message.reply_text("❌ Invalid character IDs.")
        return

    trade_data[user_id] = {
        "find_id": find_id,
        "own_id": own_id,
        "find_img": find_character["img_url"],
        "own_img": own_character["img_url"],
        "find_name": find_character["name"],
        "own_name": own_character["name"]
    }

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm", callback_data="trade_confirm_yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="trade_confirm_no")
        ]
    ])

    await message.reply_photo(
        photo=find_character["img_url"],
        caption=(
            f"⚔️ **Trade Confirmation**\n\n"
            f"You offer: **{own_character['name']}**\n"
            f"You want: **{find_character['name']}**\n\n"
            f"Confirm trade search?"
        ),
        reply_markup=keyboard
    )


# --------------------------------
# TRADE CONFIRM
# --------------------------------

@app.on_callback_query(filters.regex("^trade_confirm_"))
async def trade_confirmation(client: Client, callback_query: CallbackQuery):

    user_id = callback_query.from_user.id
    action = callback_query.data.split("_")[-1]

    if action == "no":
        await callback_query.message.edit_text("❌ Trade cancelled.")
        return

    trade_info = trade_data.get(user_id)

    if not trade_info:
        await callback_query.answer("Trade data missing.", show_alert=True)
        return

    find_id = trade_info["find_id"]

    owners = await user_collection.aggregate([
        {"$match": {"characters.id": find_id}},
        {"$unwind": "$characters"},
        {"$match": {"characters.id": find_id}},
        {"$group": {
            "_id": "$_id",
            "username": {"$first": "$username"},
            "first_name": {"$first": "$first_name"}
        }}
    ]).to_list(length=20)

    if not owners:
        await callback_query.message.edit_text("❌ No owners found.")
        return

    pagination_state[user_id] = {
        "owners": owners,
        "page": 0
    }

    await show_trade_page(callback_query.message, user_id)


# --------------------------------
# SHOW OWNER PAGE
# --------------------------------

async def show_trade_page(message: Message, user_id: int):

    state = pagination_state.get(user_id)
    trade_info = trade_data.get(user_id)

    if not state or not trade_info:
        return

    page = state["page"]
    owners = state["owners"]
    owner = owners[page]

    username = owner.get("username") or "NoUsername"

    find_img = trade_info["find_img"]

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📩 Send Request",
                callback_data=f"trade_request_{owner['_id']}"
            )
        ],
        [
            InlineKeyboardButton("⬅️", callback_data="trade_prev"),
            InlineKeyboardButton(f"{page+1}/{len(owners)}", callback_data="ignore"),
            InlineKeyboardButton("➡️", callback_data="trade_next")
        ]
    ])

    caption = (
        f"👤 Owner: **{owner['first_name']}** (@{username})\n\n"
        f"🎯 Want: **{trade_info['find_name']}**\n"
        f"💎 Offer: **{trade_info['own_name']}**"
    )

    await message.edit_media(
        InputMediaPhoto(find_img, caption=caption),
        reply_markup=keyboard
    )


# --------------------------------
# PAGINATION + REQUEST
# --------------------------------

@app.on_callback_query(filters.regex("^trade_(prev|next|request)"))
async def handle_trade_buttons(client: Client, callback_query: CallbackQuery):

    user_id = callback_query.from_user.id
    state = pagination_state.get(user_id)

    if not state:
        await callback_query.answer("Session expired.", show_alert=True)
        return

    data = callback_query.data

    if data == "trade_prev":

        if state["page"] > 0:
            state["page"] -= 1

        await show_trade_page(callback_query.message, user_id)

    elif data == "trade_next":

        if state["page"] < len(state["owners"]) - 1:
            state["page"] += 1

        await show_trade_page(callback_query.message, user_id)

    elif data.startswith("trade_request"):

        target_user_id = int(data.split("_")[-1])

        await send_trade_request(
            client,
            callback_query,
            user_id,
            target_user_id
        )


# --------------------------------
# SEND TRADE REQUEST
# --------------------------------

async def send_trade_request(client, callback_query, user_id, target_user_id):

    trade_info = trade_data.get(user_id)

    if not trade_info:
        await callback_query.answer("Trade session expired.", show_alert=True)
        return

    username = callback_query.from_user.username or "NoUsername"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Accept",
                callback_data=f"trade_accept_{user_id}"
            ),
            InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"trade_reject_{user_id}"
            )
        ]
    ])

    try:

        await client.send_photo(
            chat_id=target_user_id,
            photo=trade_info["own_img"],
            caption=(
                f"⚔️ **Trade Request**\n\n"
                f"From: {callback_query.from_user.first_name} (@{username})\n\n"
                f"🎯 Wants: {trade_info['find_name']}\n"
                f"💎 Offers: {trade_info['own_name']}"
            ),
            reply_markup=keyboard
        )

    except:

        await callback_query.answer(
            "Couldn't send request to this user.",
            show_alert=True
        )
        return

    await callback_query.message.edit_text("✅ Trade request sent!")

    # Cleanup
    trade_data.pop(user_id, None)
    pagination_state.pop(user_id, None)


# --------------------------------
# ACCEPT / REJECT
# --------------------------------

@app.on_callback_query(filters.regex("^trade_accept_"))
async def accept_trade(client, callback_query: CallbackQuery):

    requester = int(callback_query.data.split("_")[-1])

    await callback_query.message.edit_caption(
        "✅ Trade accepted!\nContact the user to complete trade."
    )

    await client.send_message(
        requester,
        "🎉 Your trade request was accepted!"
    )


@app.on_callback_query(filters.regex("^trade_reject_"))
async def reject_trade(client, callback_query: CallbackQuery):

    requester = int(callback_query.data.split("_")[-1])

    await callback_query.message.edit_caption("❌ Trade rejected.")

    await client.send_message(
        requester,
        "❌ Your trade request was rejected."
  )
