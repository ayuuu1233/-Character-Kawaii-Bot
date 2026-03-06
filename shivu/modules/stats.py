from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from shivu import collection, application, user_collection


async def show_database(update: Update, context: CallbackContext) -> None:
    # Bot owner ID(s)
    DEV_LIST = [5158013355]

    # Check if the user executing the command is authorized
    if update.effective_user.id not in DEV_LIST:
        await update.message.reply_text("🚫 You are not authorized to use this feature.")
        return

    try:
        # Ensure data fetching works and provide fallbacks
        total_characters = await collection.count_documents({}) or 0
        total_users = await user_collection.count_documents({"type": "user"}) or 0
        total_chats = await user_collection.count_documents({"type": "chat"}) or 0
        total_waifus = await collection.count_documents({"is_waifu": True}) or 0
        total_animes = len(await collection.distinct("anime")) or 0
        total_harems = await user_collection.count_documents(
            {"has_harem": {"$exists": True, "$eq": True}}
        ) or 0

        # Debug: Print results for validation
        print(
            f"Characters: {total_characters}, Users: {total_users}, Chats: {total_chats}, "
            f"Waifus: {total_waifus}, Animes: {total_animes}, Harems: {total_harems}"
        )

        # Count characters by rarity
        rarities = [
            "⚪️ Common", "🔵 Medium", "👶 Chibi", "🟠 Rare", 
            "🟡 Legendary", "💮 Exclusive", "🫧 Premium", 
            "🔮 Limited Edition", "🌸 Exotic", "🎐 Astral", "💞 Valentine"
        ]
        rarity_counts = {
            rarity: await collection.count_documents({"rarity": rarity}) or 0
            for rarity in rarities
        }

        # Construct a message to display
        message = (
            "╭───────────✧───────────╮\n"
            "        🌟 **Bot Database Summary** 🌟\n"
            "╰───────────✧───────────╯\n\n"
            f"◈ **👤 Total Characters**: `{total_characters}`\n"
            f"◈ **👥 Total Users**: `{total_users}`\n"
            f"◈ **🍜 Total Chats**: `{total_chats}`\n"
            f"◈ **🍁 Total Waifus**: `{total_waifus}`\n"
            f"◈ **🍃 Total Harems**: `{total_harems}`\n"
            f"◈ **⛩️ Total Animes**: `{total_animes}`\n"
            "────────────✧────────────\n"
            "❄️ **Character Counts by Rarity:**\n"
        )
        for rarity, count in rarity_counts.items():
            message += f"   ├─➤ {rarity}: `{count}`\n"
        message += "────────────✧────────────"

        # Inline keyboard for "Close" button
        keyboard = [[InlineKeyboardButton("❌ Close", callback_data="close_message")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the constructed message with the inline keyboard
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception as e:
        # Error handling with better feedback
        print(f"Error occurred: {e}")  # Debugging
        await update.message.reply_text(
            f"⚠️ An error occurred while fetching database data:\n`{e}`",
            parse_mode="Markdown",
        )


# Callback to handle the "Close" button
async def close_message_callback(update: Update, context: CallbackContext) -> None:
    try:
        await update.callback_query.message.delete()
    except Exception as e:
        await update.callback_query.answer(
            f"⚠️ Unable to delete the message: {e}", show_alert=True
        )


# Add the command handler to the application
application.add_handler(CommandHandler("stats", show_database, block=False))
application.add_handler(CallbackQueryHandler(close_message_callback, pattern="^close_message$"))
