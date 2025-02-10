# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import asyncio
from info import *
from utils import *
from time import time 
from plugins.generate import database
from pyrogram import Client, filters 
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message 

async def send_message_in_chunks(client, chat_id, text, reply_to_message_id=None):
    max_length = 4096
    for i in range(0, len(text), max_length):
        msg = await client.send_message(
            chat_id=chat_id,
            text=text[i:i+max_length],
            reply_to_message_id=reply_to_message_id  # Added reply feature
        )
        asyncio.create_task(delete_after_delay(msg, 1800))

async def delete_after_delay(message: Message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

@Client.on_message(filters.text & filters.group & filters.incoming & ~filters.command(["verify", "connect", "id"]))
async def search(bot, message):
    vj = database.find_one({"chat_id": ADMIN})
    if vj is None:
        return await message.reply("**Contact Admin Then Say To Login In Bot.**")
    
    User = Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID)
    await User.connect()
    
    if not await force_sub(bot, message):
        return
    
    channels = (await get_group(message.chat.id)).get("channels", [])
    if not channels:
        return
    
    if message.text.startswith("/"):
        return
    
    query = message.text
    head = f"<u>⭕ Results for your search '{query}' {message.from_user.mention} 👇\n\n💢 Powered By </u> <b><I>@VJ_Botz ❗</I></b>\n\n"
    results = ""
    
    try:
        # Maintain context by replying to original message
        reply_to_id = message.message_id
        
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name not in results:
                    results += f"<b><I>♻️ {name}\n🔗 {msg.link}</I></b>\n\n"
        
        if not results:
            movies = await search_imdb(query)
            buttons = [
                [InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}")]
                for movie in movies
            ]
            await message.reply_photo(
                photo="https://graph.org/file/c361a803c7b70fc50d435.jpg",
                caption=f"<b><I>🔍 No results found for '{query}'\n🔺 Did you mean any of these?</I></b>",
                reply_to_message_id=reply_to_id,  # Reply to original message
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await send_message_in_chunks(
                bot,
                message.chat.id,
                head+results,
                reply_to_message_id=reply_to_id  # Reply to original message
            )
            
    except Exception as e:
        await message.reply(f"Error in search: {str(e)}", reply_to_message_id=message.message_id)

@Client.on_callback_query(filters.regex(r"^recheck"))
async def recheck(bot, update):
    try:
        vj = database.find_one({"chat_id": ADMIN})
        if vj is None:
            return await update.message.edit("**Contact Admin Then Say To Login In Bot.**")
        
        User = Client("post_search", session_string=vj['session'], api_hash=API_HASH, api_id=API_ID)
        await User.connect()
        
        # Get original message context
        original_message = update.message.reply_to_message
        reply_to_id = original_message.message_id if original_message else None
        
        # Verify user
        if update.from_user.id != original_message.from_user.id:
            return await update.answer("This search isn't yours!", show_alert=True)
        
        await update.message.edit("🔍 Searching with correct title...")
        
        imdb_id = update.data.split("_")[1]
        query = await search_imdb(imdb_id)
        channels = (await get_group(update.message.chat.id)).get("channels", [])
        
        results = ""
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query):
                name = (msg.text or msg.caption).split("\n")[0]
                if name not in results:
                    results += f"<b><I>♻️🍿 {name}\n🔗 {msg.link}</I></b>\n\n"
        
        if not results:
            return await update.message.edit(
                "🔍 Still no results found!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📬 Request to Admin", callback_data=f"request_{imdb_id}")]])
            )
        
        response = f"<u>⭕ Results for '{query}' 👇\n\n💢 Powered By @VJ_Botz ❗</u>\n\n{results}"
        await send_message_in_chunks(
            bot,
            update.message.chat.id,
            response,
            reply_to_message_id=reply_to_id  # Maintain reply chain
        )
        await update.message.delete()
        
    except Exception as e:
        await update.message.edit(f"Error: {str(e)}")

@Client.on_callback_query(filters.regex(r"^request"))
async def request(bot, update):
    try:
        # Get original message context
        original_message = update.message.reply_to_message
        if update.from_user.id != original_message.from_user.id:
            return await update.answer("This request isn't yours!", show_alert=True)
        
        admin_id = (await get_group(update.message.chat.id)).get("user_id")
        imdb_id = update.data.split("_")[1]
        movie_title = await search_imdb(imdb_id)
        
        request_msg = (
            f"📬 New Request from {update.from_user.mention}\n"
            f"🗂 Title: {movie_title}\n"
            f"🔗 IMDb: https://www.imdb.com/title/tt{imdb_id}\n"
            f"💬 Original Query: {original_message.text}"
        )
        
        await bot.send_message(
            chat_id=admin_id,
            text=request_msg,
            disable_web_page_preview=True,
            reply_to_message_id=original_message.message_id  # Maintain context
        )
        
        await update.answer("✅ Request sent to admin!", show_alert=True)
        await update.message.delete()
        
    except Exception as e:
        await update.message.edit(f"Request failed: {str(e)}")
