# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on Telegram @KingVJ01

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import add_user, get_users, get_groups  # Assuming proper database functions
import script  # Assuming `script.py` contains predefined message templates

@Client.on_message(filters.command("start") & ~filters.channel)
async def start(bot, message):
    """Handles the /start command and welcomes the user."""
    try:
        database.insert_one({"chat_id": message.from_user.id})  # Store user ID in the database
    except Exception as e:
        print(f"Database Insert Error: {e}")

    bot_username = (await bot.get_me()).username  # Get bot username

    await add_user(message.from_user.id, message.from_user.first_name)  # Store user details

    buttons = [
        [InlineKeyboardButton("➕ Add Me To Your Group ➕", url=f"https://t.me/{bot_username}?startgroup=true")],
        [
            InlineKeyboardButton("Help", callback_data="misc_help"),
            InlineKeyboardButton("About", callback_data="misc_about")
        ],
        [
            InlineKeyboardButton("🤖 Updates", url="https://t.me/rmcbackup"),
            InlineKeyboardButton("🔍 Group", url="https://t.me/rmcmovierequest")
        ]
    ]

    await message.reply(
        text=script.START.format(message.from_user.mention),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.command("help"))
async def help(bot, message):
    """Handles the /help command."""
    await message.reply(text=script.HELP, disable_web_page_preview=True)

@Client.on_message(filters.command("about"))
async def about(bot, message):
    """Handles the /about command."""
    bot_mention = (await bot.get_me()).mention
    await message.reply(text=script.ABOUT.format(bot_mention), disable_web_page_preview=True)

@Client.on_message(filters.command("stats"))
async def stats(bot, message):
    """Handles the /stats command to show bot usage statistics."""
    user_count, _ = await get_users()
    group_count, _ = await get_groups()
    
    await message.reply(script.STATS.format(user_count, group_count))

@Client.on_message(filters.command("id"))
async def id(bot, message):
    """Handles the /id command to retrieve chat and user IDs."""
    text = f"**Current Chat ID:** `{message.chat.id}`\n"

    if message.from_user:
        text += f"**Your ID:** `{message.from_user.id}`\n"

    if message.reply_to_message:
        replied_user = message.reply_to_message.from_user
        if replied_user:
            text += f"**Replied User ID:** `{replied_user.id}`\n"

        if message.reply_to_message.forward_from:
            text += f"**Forwarded From User ID:** `{message.reply_to_message.forward_from.id}`\n"

        if message.reply_to_message.forward_from_chat:
            text += f"**Forwarded From Chat ID:** `{message.reply_to_message.forward_from_chat.id}`\n"

    await message.reply(text)

@Client.on_callback_query(filters.regex(r"^misc_(help|about|home)"))
async def misc(bot, query):
    """Handles inline button interactions."""
    data = query.data.split("_")[-1]
    bot_username = (await bot.get_me()).username

    if data == "home":
        buttons = [
            [InlineKeyboardButton("➕ Add Me To Your Group ➕", url=f"https://t.me/{bot_username}?startgroup=true")],
            [
                InlineKeyboardButton("Help", callback_data="misc_help"),
                InlineKeyboardButton("About", callback_data="misc_about")
            ],
            [
                InlineKeyboardButton("🤖 Updates", url="https://t.me/rmcbackup"),
                InlineKeyboardButton("🔍 Group", url="https://t.me/rmcmovierequest")
            ]
        ]
        text = script.START.format(query.from_user.mention)

    elif data == "help":
        buttons = [[InlineKeyboardButton("⬅️ Back", callback_data="misc_home")]]
        text = script.HELP

    elif data == "about":
        buttons = [[InlineKeyboardButton("⬅️ Back", callback_data="misc_home")]]
        text = script.ABOUT.format((await bot.get_me()).mention)

    await query.message.edit(text=text, disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))
